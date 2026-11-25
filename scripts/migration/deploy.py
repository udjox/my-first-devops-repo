from common import *
# Оба Compose-файла используют один project name: старый db-mysql является orphan.
compose('prod','up','-d','--build','--remove-orphans','--wait','--wait-timeout','180',log=ARTIFACTS/'deployment.log')
wait_http(420)
print('Mattermost production API is responding',flush=True)
