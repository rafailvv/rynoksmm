DC_FILES = -f docker-compose.smm.yml \
           -f docker-compose.massage.yml \
           -f docker-compose.event.yml
           


up-logs:
	docker-compose $(DC_FILES) up $(NAME)
	docker-compose -f docker-compose.nginx.yml up nginx

up:
	docker-compose $(DC_FILES) up -d $(NAME)
	docker-compose -f docker-compose.nginx.yml up -d nginx

down:
	docker-compose $(DC_FILES) down $(NAME)
	docker-compose -f docker-compose.nginx.yml down nginx

logs:
	docker-compose $(DC_FILES) -f docker-compose.nginx.yml logs -f --tail 300 $(NAME) 

ps:
	docker-compose $(DC_FILES) -f docker-compose.nginx.yml ps

build:
	docker-compose $(DC_FILES) build $(NAME)
	docker-compose -f docker-compose.nginx.yml build nginx


smm:
	@if [ "$(ACTION)" = "up" ]; then docker-compose -f docker-compose.minio.yml up -d minio; fi
	docker-compose $(DC_FILES) $(ACTION) $(if $(filter up,$(ACTION)),-d) $(if $(filter build,$(ACTION)),bot_smm web_smm,bot_smm web_smm redis_smm db_smm)


massage:
	@if [ "$(ACTION)" = "up" ]; then docker-compose -f docker-compose.minio.yml up -d minio; fi
	docker-compose $(DC_FILES) $(ACTION) $(if $(filter up,$(ACTION)),-d) $(if $(filter build,$(ACTION)),bot_massage web_massage,bot_massage web_massage redis_massage db_massage)

event:
	@if [ "$(ACTION)" = "up" ]; then docker-compose -f docker-compose.minio.yml up -d minio; fi
	docker-compose $(DC_FILES) $(ACTION) $(if $(filter up,$(ACTION)),-d) $(if $(filter build,$(ACTION)),bot_event web_event,bot_event web_event redis_event db_event)


nginx:
	docker-compose $(DC_FILES) $(ACTION) $(if $(filter up,$(ACTION)),-d) nginx

minio:
	docker-compose -f docker-compose.minio.yml $(ACTION) $(if $(filter up,$(ACTION)),-d) minio

minio-logs:
	docker-compose -f docker-compose.minio.yml logs -f minio

minio-ps:
	docker-compose -f docker-compose.minio.yml ps

minio-build:
	docker-compose -f docker-compose.minio.yml build minio

minio-down:
	docker-compose -f docker-compose.minio.yml down minio

minio-up:
	docker-compose -f docker-compose.minio.yml up -d minio

restart:
	sudo docker-compose -f docker-compose.minio.yml up -d minio
	sudo docker-compose $(DC_FILES) down
	sudo docker-compose $(DC_FILES) build
	sudo docker-compose $(DC_FILES) up -d


bot-restart:
	sudo docker-compose -f docker-compose.minio.yml up -d minio
	sudo docker-compose $(DC_FILES) down bot_massage bot_smm bot_event
	sudo docker-compose $(DC_FILES) build bot_massage bot_smm bot_event
	sudo docker-compose $(DC_FILES) up -d bot_massage bot_smm bot_event

minio-restart:
	sudo docker-compose -f docker-compose.minio.yml down minio
	sudo docker-compose -f docker-compose.minio.yml build minio
	sudo docker-compose -f docker-compose.minio.yml up -d minio

nginx-restart:
	sudo docker-compose -f docker-compose.nginx.yml down nginx
	sudo docker-compose -f docker-compose.nginx.yml build nginx
	sudo docker-compose -f docker-compose.nginx.yml up -d nginx

restart-nf:
	sudo docker-compose -f docker-compose.minio.yml up -d minio
	sudo docker-compose $(DC_FILES) build bot_massage web_massage bot_smm web_smm bot_event web_event
	sudo docker-compose $(DC_FILES) up -d bot_massage web_massage bot_smm web_smm bot_event web_event
	sudo docker-compose -f docker-compose.nginx.yml up -d nginx



smm-logs:
	docker-compose -f docker-compose.smm.yml logs -f --tail 300 bot_smm web_smm

massage-logs:
	docker-compose -f docker-compose.massage.yml logs -f --tail 300 bot_massage web_massage

event-logs:
	docker-compose -f docker-compose.photo.yml logs -f --tail 300 bot_event web_event
