-- 1. Tabla de Usuarios
CREATE TABLE usuarios (
    id_usuario SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    fecha_registro DATE DEFAULT CURRENT_DATE,
    pais VARCHAR(50)
);

-- 2. Tabla de Publicaciones (Posts)
CREATE TABLE publicaciones (
    id_publicacion SERIAL PRIMARY KEY,
    texto_contenido TEXT,
    fecha_publicacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    likes_contador INT DEFAULT 0,
    autor_id INT NOT NULL -- Campo huérfano de relación
);

-- 3. Tabla de Comentarios
CREATE TABLE comentarios (
    id_comentario SERIAL PRIMARY KEY,
    contenido VARCHAR(255),
    fecha_comentario TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    usuario_id INT NOT NULL,
    publicacion_id INT NOT NULL -- Campos huérfanos de relación
);

-- 4. Tabla de Amistades (Relación Muchos a Muchos)
CREATE TABLE amistades (
    id_amistad SERIAL PRIMARY KEY,
    fecha_amistad DATE DEFAULT CURRENT_DATE,
    estado VARCHAR(20), -- Ej: 'ACEPTADA', 'PENDIENTE'
    usuario_solicitante_id INT NOT NULL,
    usuario_receptor_id INT NOT NULL -- Campos huérfanos de relación
);