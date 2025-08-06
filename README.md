# Photostream-album-sync
Microservice to sync image files from a photoprism album into a folder which then can be used as content for photo-stream

This is how I use it: https://riess.dev/photostream/

## Docker
Just use the `docker-compose.yaml` file from this repo. You can either build the image yourself using the `Dockerfile` or use the [image on Docker Hub](https://hub.docker.com/repository/docker/valentinriess/) `valentinriess/photostream-album-sync`

## Setup Triggers
### Immich
Connect to your immich postgres and create a function and trigger for changes on the `album_asset` table. The service will listen on the `albums` channel.

#### Create function
```sql
CREATE OR REPLACE FUNCTION notify_albums_change() RETURNS trigger AS $trigger$
DECLARE
  rec album_asset;
  dat album_asset;
  payload TEXT;
BEGIN

  -- Set record row depending on operation
  CASE TG_OP
  WHEN 'UPDATE' THEN
     rec := NEW;
     dat := OLD;
  WHEN 'INSERT' THEN
     rec := NEW;
  WHEN 'DELETE' THEN
     rec := OLD;
  ELSE
     RAISE EXCEPTION 'Unknown TG_OP: "%". Should not occur!', TG_OP;
  END CASE;

  -- Build the payload
  payload := json_build_object('timestamp',CURRENT_TIMESTAMP,'action',LOWER(TG_OP),'db_schema',TG_TABLE_SCHEMA,'table',TG_TABLE_NAME,'record',row_to_json(rec), 'old',row_to_json(dat));

  -- Notify the channel
  PERFORM pg_notify('albums', payload);

  RETURN rec;
END;
$trigger$ LANGUAGE plpgsql;
```

#### Create trigger
```sql
CREATE TRIGGER albums_notify AFTER INSERT OR UPDATE OR DELETE 
ON album_asset
FOR EACH ROW EXECUTE PROCEDURE notify_albums_change();
```

### Photoprism
Find the folder where photoprism stores your album sidecar yaml file. It should be located in `storage/albums/album`. Mount it into the docker container and configure the `PHOTOPRISM_SYNC_ALBUM_PATH` environment variable accordingly.

Example: `PHOTOPRISM_ALBUM_PATH=/app/data/arqp4pz1fwptx4oq.yml`

The service will watch this file for changes.
