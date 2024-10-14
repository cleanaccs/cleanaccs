#!/bin/zsh

docker exec postgres pg_dump -U postgres messages_db > ./data/messages_db_dump.sql
