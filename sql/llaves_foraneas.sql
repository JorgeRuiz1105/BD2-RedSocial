-- Relacionar publicaciones con su autor
ALTER TABLE publicaciones
ADD CONSTRAINT fk_publicacion_usuario
FOREIGN KEY (autor_id) REFERENCES usuarios(id_usuario);

-- Relacionar comentarios con usuario y publicación
ALTER TABLE comentarios
ADD CONSTRAINT fk_comentario_usuario
FOREIGN KEY (usuario_id) REFERENCES usuarios(id_usuario);

ALTER TABLE comentarios
ADD CONSTRAINT fk_comentario_publicacion
FOREIGN KEY (publicacion_id) REFERENCES publicaciones(id_publicacion);

-- Relacionar amistades con los usuarios involucrados
ALTER TABLE amistades
ADD CONSTRAINT fk_amistad_solicitante
FOREIGN KEY (usuario_solicitante_id) REFERENCES usuarios(id_usuario);

ALTER TABLE amistades
ADD CONSTRAINT fk_amistad_receptor
FOREIGN KEY (usuario_receptor_id) REFERENCES usuarios(id_usuario);