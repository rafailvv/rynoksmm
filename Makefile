DC_FILES = -f docker-compose.smm.yml \
           -f docker-compose.massage.yml \
           -f docker-compose.event.yml

SERVICE_TARGETS = smm massage event
SERVICE_ACTIONS = up build down logs
PRIMARY_GOAL = $(firstword $(MAKECMDGOALS))
ACTION_GOAL = $(word 2,$(MAKECMDGOALS))

ifneq ($(filter $(PRIMARY_GOAL),$(SERVICE_TARGETS)),)
ifneq ($(filter $(ACTION_GOAL),$(SERVICE_ACTIONS)),)
ACTION ?= $(ACTION_GOAL)
SERVICE_ACTION_MODE = 1
endif
endif

.PHONY: up-logs up down logs ps build smm massage event nginx minio \
        minio-logs minio-ps minio-build minio-down minio-up restart \
        bot-restart minio-restart nginx-restart restart-nf \
        smm-logs massage-logs event-logs

define check_service_action
	@if [ -z "$(ACTION)" ]; then \
		echo "Usage: make $@ <up|build|down|logs> or make $@ ACTION=<up|build|down|logs>"; \
		exit 2; \
	fi
	@case "$(ACTION)" in \
		up|build|down|logs) ;; \
		*) echo "Unknown action: $(ACTION). Use: up, build, down, logs"; exit 2 ;; \
	esac
endef


up-logs:
	docker-compose $(DC_FILES) up $(NAME)
	docker-compose -f docker-compose.nginx.yml up nginx

up:
ifeq ($(SERVICE_ACTION_MODE),1)
	@:
else
	docker-compose $(DC_FILES) up -d $(NAME)
	docker-compose -f docker-compose.nginx.yml up -d nginx
endif

down:
ifeq ($(SERVICE_ACTION_MODE),1)
	@:
else
	docker-compose $(DC_FILES) down $(NAME)
	docker-compose -f docker-compose.nginx.yml down nginx
endif

logs:
ifeq ($(SERVICE_ACTION_MODE),1)
	@:
else
	docker-compose $(DC_FILES) -f docker-compose.nginx.yml logs -f --tail 300 $(NAME) 
endif

ps:
	docker-compose $(DC_FILES) -f docker-compose.nginx.yml ps

build:
ifeq ($(SERVICE_ACTION_MODE),1)
	@:
else
	docker-compose $(DC_FILES) build $(NAME)
	docker-compose -f docker-compose.nginx.yml build nginx
endif


smm:
	$(call check_service_action)
	@if [ "$(ACTION)" = "up" ]; then docker-compose -f docker-compose.minio.yml up -d minio; fi
	docker-compose $(DC_FILES) $(ACTION) $(if $(filter up,$(ACTION)),-d) $(if $(filter logs,$(ACTION)),-f --tail 300) $(if $(filter build logs,$(ACTION)),bot_smm web_smm,bot_smm web_smm redis_smm db_smm)


massage:
	$(call check_service_action)
	@if [ "$(ACTION)" = "up" ]; then docker-compose -f docker-compose.minio.yml up -d minio; fi
	docker-compose $(DC_FILES) $(ACTION) $(if $(filter up,$(ACTION)),-d) $(if $(filter logs,$(ACTION)),-f --tail 300) $(if $(filter build logs,$(ACTION)),bot_massage web_massage,bot_massage web_massage redis_massage db_massage)

event:
	$(call check_service_action)
	@if [ "$(ACTION)" = "up" ]; then docker-compose -f docker-compose.minio.yml up -d minio; fi
	docker-compose $(DC_FILES) $(ACTION) $(if $(filter up,$(ACTION)),-d) $(if $(filter logs,$(ACTION)),-f --tail 300) $(if $(filter build logs,$(ACTION)),bot_event web_event,bot_event web_event redis_event db_event)


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
	docker-compose -f docker-compose.event.yml logs -f --tail 300 bot_event web_event
