package main

import (
	"context"
	"database/sql"
	"encoding/json"
	"fmt"
	_ "github.com/lib/pq"
	"log"
	"net"
	"net/http"
	"net/url"
	"os"
	"time"
)

type Item struct {
	ID   int    `json:"id"`
	Name string `json:"name"`
}

func env(key, fallback string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return fallback
}
func main() {
	if len(os.Args) > 1 && os.Args[1] == "healthcheck" {
		client := &http.Client{Timeout: 2 * time.Second}
		res, err := client.Get("http://127.0.0.1:" + env("HTTP_PORT", "8080") + "/healthz")
		if err != nil {
			log.Print(err)
			os.Exit(1)
		}
		defer res.Body.Close()
		if res.StatusCode != http.StatusOK {
			os.Exit(1)
		}
		return
	}
	dsn := &url.URL{Scheme: "postgres", Host: net.JoinHostPort(env("DB_HOST", "db"), env("DB_PORT", "5432")), Path: "/" + env("DB_NAME", "appdb"), User: url.UserPassword(env("DB_USER", "app"), os.Getenv("DB_PASSWORD"))}
	q := dsn.Query()
	q.Set("sslmode", "disable")
	q.Set("connect_timeout", "3")
	dsn.RawQuery = q.Encode()
	db, err := sql.Open("postgres", dsn.String())
	if err != nil {
		log.Fatal(err)
	}
	defer db.Close()
	db.SetMaxOpenConns(10)
	db.SetMaxIdleConns(5)
	db.SetConnMaxLifetime(5 * time.Minute)
	ready := false
	for i := 0; i < 30; i++ {
		ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
		err = db.PingContext(ctx)
		cancel()
		if err == nil {
			ready = true
			break
		}
		time.Sleep(2 * time.Second)
	}
	if !ready {
		log.Fatal("database unavailable: ", err)
	}
	log.Print("database connected")
	mux := http.NewServeMux()
	mux.HandleFunc("/healthz", func(w http.ResponseWriter, r *http.Request) {
		ctx, cancel := context.WithTimeout(r.Context(), time.Second)
		defer cancel()
		if err := db.PingContext(ctx); err != nil {
			http.Error(w, "database unavailable", 503)
			return
		}
		fmt.Fprintln(w, "ok")
	})
	mux.HandleFunc("/api/items", func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodGet {
			w.Header().Set("Allow", "GET")
			http.Error(w, "method not allowed", 405)
			return
		}
		ctx, cancel := context.WithTimeout(r.Context(), 3*time.Second)
		defer cancel()
		rows, err := db.QueryContext(ctx, "SELECT id, name FROM items ORDER BY id")
		if err != nil {
			log.Print("items query: ", err)
			http.Error(w, "database query failed", 500)
			return
		}
		defer rows.Close()
		items := []Item{}
		for rows.Next() {
			var it Item
			if err := rows.Scan(&it.ID, &it.Name); err != nil {
				log.Print(err)
				http.Error(w, "database read failed", 500)
				return
			}
			items = append(items, it)
		}
		if err := rows.Err(); err != nil {
			log.Print(err)
			http.Error(w, "database read failed", 500)
			return
		}
		w.Header().Set("Content-Type", "application/json; charset=utf-8")
		if err := json.NewEncoder(w).Encode(items); err != nil {
			log.Print(err)
		}
	})
	// FileServer сам обрабатывает index.html без ручной подмены URL.
	mux.Handle("/", http.FileServer(http.Dir(env("STATIC_DIR", "/app/static"))))
	server := &http.Server{Addr: ":" + env("HTTP_PORT", "8080"), Handler: mux, ReadHeaderTimeout: 5 * time.Second, ReadTimeout: 10 * time.Second, WriteTimeout: 10 * time.Second, IdleTimeout: 60 * time.Second}
	log.Printf("listening on %s", server.Addr)
	log.Fatal(server.ListenAndServe())
}
