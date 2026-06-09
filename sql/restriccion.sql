-- Esto evita que un id de usuario sea igual al otro en la misma fila
ALTER TABLE amistades
ADD CONSTRAINT chk_sin_auto_amistad
CHECK (usuario_solicitante_id != usuario_receptor_id);