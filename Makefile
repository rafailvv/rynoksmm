DC_FILES = -f docker-compose.smm.yml \
           -f docker-compose.massage.yml \
           -f docker-compose.nginx.yml


up:
	docker-compose $(DC_FILES) up -d $(NAME)

down:
	docker-compose $(DC_FILES) down $(NAME)

logs:
	docker-compose $(DC_FILES) logs -f $(NAME)
ps:
	docker-compose $(DC_FILES) ps

build:
	docker-compose $(DC_FILES) build $(NAME)


smm:
	docker-compose $(DC_FILES) $(ACTION) $(if $(filter up,$(ACTION)),-d) $(if $(filter build,$(ACTION)),bot_smm web_smm,bot_smm web_smm redis_smm db_smm)


massage:
	docker-compose $(DC_FILES) $(ACTION) $(if $(filter up,$(ACTION)),-d) $(if $(filter build,$(ACTION)),bot_massage web_massage,bot_massage web_massage redis_massage db_massage)


nginx:
	docker-compose $(DC_FILES) $(ACTION) $(if $(filter up,$(ACTION)),-d) nginx
