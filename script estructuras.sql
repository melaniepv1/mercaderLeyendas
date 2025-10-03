CREATE DATABASE mercaderleyendas
    WITH
    OWNER = mercader_user
    ENCODING = 'UTF8'
    LOCALE_PROVIDER = 'libc'
    CONNECTION LIMIT = -1
    IS_TEMPLATE = False;


--- Luego de crear la base de datos, se debe conectar a ella para crear el esquema y las tablas, desde ---
--- pgAdmin, abren la nueva base de datos y el query tool de la misma, ahí ejecutan el resto del código ---

CREATE SCHEMA sch_mercaderleyendas AUTHORIZATION mercader_user;
-- Permitir usar el esquema (por si otros usuarios también lo necesitan)
GRANT USAGE ON SCHEMA sch_mercaderleyendas TO mercader_user;

SET search_path TO sch_mercaderleyendas;
-- TABLAS --

CREATE TABLE ciudad (
    id_ciudad SERIAL PRIMARY KEY,
    nombre_ciudad VARCHAR(20),
    coordenada_x INT,
    coordenada_y INT,
    tiene_puerto BOOLEAN,
    alejada_de_costa BOOLEAN
);

CREATE TABLE producto (
    id_producto SERIAL PRIMARY KEY,
    nombre_producto VARCHAR(50),
    peso_producto NUMERIC,
    tipo_producto VARCHAR(20) CHECK (tipo_producto IN ('logistica', 'comercial', 'herramientas')),
    unidad VARCHAR(10),        
    costo_terrestre NUMERIC,  
    costo_maritimo NUMERIC,   
    cantidad_unidad NUMERIC            
);

CREATE TABLE ruta (
    id_ruta SERIAL PRIMARY KEY,
    id_ciudad_origen INT REFERENCES ciudad(id_ciudad),
    id_ciudad_destino INT REFERENCES ciudad(id_ciudad),
    tipo_transporte VARCHAR(20) CHECK (tipo_transporte IN ('terrestre', 'marítimo')),
    semanas_distancia INT,
    unidireccional BOOLEAN,
    personal_minimo INT,
    personal_maximo INT
);

CREATE TABLE evento (
    id_evento SERIAL PRIMARY KEY,
    nombre_evento VARCHAR(50),
    tipo_evento VARCHAR(20) CHECK (tipo_evento IN ('social', 'ambiental')),
    descripcion_evento VARCHAR(255)
);

CREATE TABLE jugador (
    id_jugador SERIAL PRIMARY KEY,
    nombre_usuario VARCHAR(50) UNIQUE
);

CREATE TABLE personaje (
    id_personaje SERIAL PRIMARY KEY,
    nombre_personaje VARCHAR(20),
    id_ciudad_actual INT REFERENCES ciudad(id_ciudad),
    id_jugador INT REFERENCES jugador(id_jugador)
);

CREATE TABLE habilidad (
    id_habilidad SERIAL PRIMARY KEY,
    nombre_habilidad VARCHAR(100),
    efecto_habilidad TEXT,
    tipo_habilidad VARCHAR(20) CHECK (tipo_habilidad IN ('general', 'específica')),
    personaje_asociado VARCHAR(50) CHECK (personaje_asociado IN ('Kiran', 'Leena') OR personaje_asociado IS NULL)
);


CREATE TABLE logro (
    id_logro SERIAL PRIMARY KEY,
    nombre_logro VARCHAR(50),
    beneficio_logro TEXT,
    condicion_logro VARCHAR(100)
);

CREATE TABLE transaccion (
    id_transaccion SERIAL PRIMARY KEY,
    id_jugador INT REFERENCES jugador(id_jugador),
    id_ciudad INT REFERENCES ciudad(id_ciudad),
    id_producto INT REFERENCES producto(id_producto),
    cantidad_productos_transaccion INT,
    precio_unitario NUMERIC,
    tipo_transporte VARCHAR(20) CHECK (tipo_transporte IN ('terrestre', 'marítimo')),
    tipo_transaccion VARCHAR(20) CHECK (tipo_transaccion IN ('compra', 'venta'))
);

CREATE TABLE partida (
    id_partida SERIAL PRIMARY KEY,
    id_jugador INT REFERENCES jugador(id_jugador),
    estado_partida VARCHAR(20) CHECK (estado_partida IN ('activa', 'finalizada', 'pausada')),
    fecha_inicio_partida DATE,
    fecha_fin_partida DATE,
    velocidad_juego NUMERIC,
    razon_fin VARCHAR(40) CHECK (razon_fin IN ('tiempo agotado', 'sin recursos', 'manual', 'todas las caravanas completadas')),
    caravanas_completadas INT,
    recursos_restantes TEXT,
    semana_actual INT DEFAULT 1,
    ranking_final INT
);


CREATE TABLE caravana (
    id_caravana SERIAL PRIMARY KEY,
    id_partida INT REFERENCES partida(id_partida),
    id_ruta INT REFERENCES ruta(id_ruta),
    estado_caravana VARCHAR(20) CHECK (estado_caravana IN ('en ruta', 'fallida', 'exitosa')),
    personal INT
);

CREATE TABLE inventario (
    id_producto INT REFERENCES producto(id_producto),
    id_jugador INT REFERENCES jugador(id_jugador),
    PRIMARY KEY (id_jugador, id_producto),
    cantidad_productos INT
);

CREATE TABLE producto_inicial (
    id_partida INT REFERENCES partida(id_partida),
    id_producto INT REFERENCES producto(id_producto),
    PRIMARY KEY (id_partida, id_producto)
);

CREATE TABLE viaje (
    id_viaje SERIAL PRIMARY KEY,
    id_jugador INT REFERENCES jugador(id_jugador),
    tipo_viaje VARCHAR(20) CHECK (tipo_viaje IN ('terrestre', 'marítimo')),
    duracion_viaje INT,
    id_ruta INT REFERENCES ruta(id_ruta),
    id_caravana INT REFERENCES caravana(id_caravana),
    fecha_inicio DATE
);

CREATE TABLE bitacora (
    id_bitacora SERIAL PRIMARY KEY,
    id_jugador INT REFERENCES jugador(id_jugador),
    entidad_afectada VARCHAR(50),
    id_entidad_afectada INT,
    accion VARCHAR(10) CHECK (accion IN ('INSERT', 'UPDATE', 'DELETE')),
    fecha TIMESTAMP
);

CREATE TABLE puesto_comercial (
    id_personaje INT REFERENCES personaje(id_personaje),
    id_ciudad INT REFERENCES ciudad(id_ciudad),
    PRIMARY KEY (id_personaje, id_ciudad)
);

CREATE TABLE producto_logistico_consumo (
    id_producto_logistico INT PRIMARY KEY,
    consumo_tierra_por_persona_por_dia FLOAT,
    consumo_mar_por_persona_por_dia FLOAT,
    FOREIGN KEY (id_producto_logistico) REFERENCES producto(id_producto)
);



-- ATRIBUTOS CALCULADOSS --

-- total_precio --

CREATE VIEW sch_mercaderleyendas.vista_transacciones_con_total AS
SELECT
    *,
    cantidad_productos_transaccion * precio_unitario AS total_precio
FROM sch_mercaderleyendas.transaccion;


-- años_transcurridos --

CREATE OR REPLACE VIEW sch_mercaderleyendas.vista_partidas_con_anios AS
SELECT
    id_partida,
    id_jugador,
    fecha_inicio_partida,
    fecha_fin_partida,
    velocidad_juego,
    ROUND(
        (EXTRACT(EPOCH FROM AGE(fecha_fin_partida, fecha_inicio_partida)) / 86400) / (velocidad_juego * 7 * 52),
        2
    ) AS anos_transcurridos
FROM sch_mercaderleyendas.partida;



-- TABLAS INTERMEDIARIAS --

CREATE TABLE ciudad_produce_producto (
    id_ciudad INT REFERENCES ciudad(id_ciudad),
    id_producto INT REFERENCES producto(id_producto),
    PRIMARY KEY (id_ciudad, id_producto)
);

CREATE TABLE ciudad_consume_producto (
    id_ciudad INT REFERENCES ciudad(id_ciudad),
    id_producto INT REFERENCES producto(id_producto),
    PRIMARY KEY (id_ciudad, id_producto)
);

CREATE TABLE precio_producto (
    id_ciudad INT REFERENCES ciudad(id_ciudad),
    id_producto INT REFERENCES producto(id_producto),
    precio_base NUMERIC,
    PRIMARY KEY (id_ciudad, id_producto)
);

CREATE TABLE evento_producto (
    id_evento INT REFERENCES evento(id_evento),
    id_producto INT REFERENCES producto(id_producto),
    ajuste_precio NUMERIC,
    tipo_ajuste VARCHAR(10) CHECK (tipo_ajuste IN ('compra', 'venta')),
    PRIMARY KEY (id_evento, id_producto, tipo_ajuste)
);

CREATE TABLE evento_ciudad (
    id_evento INT REFERENCES evento(id_evento),
    id_ciudad INT REFERENCES ciudad(id_ciudad),
    PRIMARY KEY (id_evento, id_ciudad)
);

CREATE TABLE jugador_habilidad (
    id_jugador INT REFERENCES jugador(id_jugador),
    id_habilidad INT REFERENCES habilidad(id_habilidad),
    estado_habilidad VARCHAR(20) CHECK (estado_habilidad IN ('activa', 'inactiva')),
    fecha_desbloqueo DATE,
    PRIMARY KEY (id_jugador, id_habilidad)
);

CREATE TABLE personaje_logro (
    id_personaje INT REFERENCES personaje(id_personaje),
    id_logro INT REFERENCES logro(id_logro),
    fecha_logro DATE,
    PRIMARY KEY (id_personaje, id_logro)
);

CREATE TABLE producto_caravana (
    id_caravana INT REFERENCES caravana(id_caravana),
    id_producto INT REFERENCES producto(id_producto),
    cantidad_producto INT,
    PRIMARY KEY (id_caravana, id_producto)
);

CREATE TABLE caravana_producto_consumido (
    id_caravana INT REFERENCES caravana(id_caravana),
    id_producto INT REFERENCES producto(id_producto),
    cantidad NUMERIC,
    PRIMARY KEY (id_caravana, id_producto)
);



-- FUNCIÓN DE VALIDACIÓN PARA PRODUCTOS LOGÍSTICOS EN caravana_producto_consumido --
CREATE OR REPLACE FUNCTION validar_producto_logistico()
RETURNS TRIGGER AS $$
DECLARE
    tipo TEXT;
BEGIN
    SELECT tipo_producto INTO tipo
    FROM sch_mercaderleyendas.producto
    WHERE id_producto = NEW.id_producto;

    IF tipo <> 'logistica' THEN
        RAISE EXCEPTION 'Solo se permiten productos logísticos (agua, vino, carne) en esta tabla.';
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;




-- PERMISOS SOBRE LAS TABLAS --
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA sch_mercaderleyendas TO mercader_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA sch_mercaderleyendas TO mercader_user;



-- FUNCIONES, VISTAS Y TRIGGERS PARA MECÁNICAS DEL JUEGO -- 


-- Mecánica 1: Fluctuación de precios según eventos activos en una ciudad --

-- Vista que ajusta el precio base de los productos considerando los eventos vinculados --

-- Vista para precios de COMPRA ajustados
CREATE OR REPLACE VIEW vista_precios_compra_ajustados AS
SELECT 
    pp.id_ciudad,
    pp.id_producto,
    pp.precio_base + COALESCE(SUM(ep.ajuste_precio), 0) AS precio_compra_ajustado
FROM precio_producto pp
LEFT JOIN evento_ciudad ec ON ec.id_ciudad = pp.id_ciudad
LEFT JOIN evento_producto ep ON ep.id_evento = ec.id_evento AND ep.id_producto = pp.id_producto
WHERE ep.tipo_ajuste = 'compra'
GROUP BY pp.id_ciudad, pp.id_producto, pp.precio_base;

-- Vista para precios de VENTA ajustados
CREATE OR REPLACE VIEW vista_precios_venta_ajustados AS
SELECT 
    pp.id_ciudad,
    pp.id_producto,
    pp.precio_base + COALESCE(SUM(ep.ajuste_precio), 0) AS precio_venta_ajustado
FROM precio_producto pp
LEFT JOIN evento_ciudad ec ON ec.id_ciudad = pp.id_ciudad
LEFT JOIN evento_producto ep ON ep.id_evento = ec.id_evento AND ep.id_producto = pp.id_producto
WHERE ep.tipo_ajuste = 'venta'
GROUP BY pp.id_ciudad, pp.id_producto, pp.precio_base;



-- Mecánica 2: Descuento o aumento según habilidades activas del jugador --

-- Función que aevalúa qué habilidades tiene activas el jugador y aplica efectos en el precio según si se trata de una compra o una venta --

CREATE OR REPLACE FUNCTION aplicar_modificador_precio(
    id_jugador INT,
    precio_base NUMERIC,
    tipo_operacion VARCHAR,
    id_producto INT,
    id_ciudad INT
) RETURNS NUMERIC AS $$
DECLARE
    nombre_habilidad TEXT;
    descuento_total NUMERIC := 0;
    aumento_total NUMERIC := 0;
    demanda_alta BOOLEAN := FALSE;
BEGIN
    -- Verificar si el producto tiene alta demanda en la ciudad
    -- (se usa precio >= 10 como criterio de alta demanda)
    SELECT EXISTS (
        SELECT 1
        FROM ciudad_consume_producto ccp
        JOIN precio_producto pp ON ccp.id_ciudad = pp.id_ciudad AND ccp.id_producto = pp.id_producto
        WHERE ccp.id_ciudad = id_ciudad
        AND ccp.id_producto = id_producto
        AND pp.precio_base >= 10
    ) INTO demanda_alta;

    -- Recorrer habilidades activas del jugador
    FOR nombre_habilidad IN
        SELECT h.nombre_habilidad
        FROM jugador_habilidad jh
        JOIN habilidad h ON jh.id_habilidad = h.id_habilidad
        WHERE jh.id_jugador = id_jugador
        AND jh.estado_habilidad = 'activa'
    LOOP
        IF tipo_operacion = 'compra' THEN
            IF nombre_habilidad = 'Negociación Avanzada' THEN
                descuento_total := descuento_total + 0.10;
            ELSIF nombre_habilidad = 'Red de Contactos' THEN
                descuento_total := descuento_total + 0.15;
            END IF;

        ELSIF tipo_operacion = 'venta' THEN
            IF nombre_habilidad = 'Negociación Avanzada' THEN
                aumento_total := aumento_total + 0.10;
            ELSIF nombre_habilidad = 'Comercio Avanzado' THEN
                aumento_total := aumento_total + 0.15;
            ELSIF nombre_habilidad = 'Inversión Inteligente' AND demanda_alta THEN
                aumento_total := aumento_total + 0.20;
            END IF;
        END IF;
    END LOOP;

    -- Aplicar el resultado final
    IF tipo_operacion = 'compra' THEN
        RETURN precio_base * (1 - descuento_total);
    ELSIF tipo_operacion = 'venta' THEN
        RETURN precio_base * (1 + aumento_total);
    ELSE
        RETURN precio_base;
    END IF;
END;
$$ LANGUAGE plpgsql;



-- Mecánica 3: Evaluar si una caravana tuvo éxito o fracasó al finalizar el viaje --

-- Actualiza el estado de la caravana y elimina la mercancía en caso de fracaso --

CREATE OR REPLACE FUNCTION sch_mercaderleyendas.evaluar_mision(p_id_viaje INT)
RETURNS TEXT AS $$
DECLARE
    v_id_car INT;
    v_id_jugador INT;
    cantidad_agua NUMERIC := 0;
    cantidad_carne NUMERIC := 0;
    cantidad_vino NUMERIC := 0;
BEGIN
    -- Obtener ID de la caravana y del jugador
    SELECT v.id_caravana, v.id_jugador INTO v_id_car, v_id_jugador
    FROM sch_mercaderleyendas.viaje v
    WHERE v.id_viaje = p_id_viaje;

    -- Obtener cantidades actuales en el inventario
    SELECT 
        COALESCE(SUM(CASE WHEN LOWER(p.nombre_producto) = 'agua' THEN i.cantidad_productos ELSE 0 END), 0),
        COALESCE(SUM(CASE WHEN LOWER(p.nombre_producto) = 'carne' THEN i.cantidad_productos ELSE 0 END), 0),
        COALESCE(SUM(CASE WHEN LOWER(p.nombre_producto) = 'vino' THEN i.cantidad_productos ELSE 0 END), 0)
    INTO cantidad_agua, cantidad_carne, cantidad_vino
    FROM sch_mercaderleyendas.inventario i
    JOIN sch_mercaderleyendas.producto p ON i.id_producto = p.id_producto
    WHERE i.id_jugador = v_id_jugador;

    -- Evaluar éxito o fracaso según inventario
    IF cantidad_agua > 0 AND cantidad_carne > 0 AND cantidad_vino > 0 THEN
        UPDATE sch_mercaderleyendas.caravana 
        SET estado_caravana = 'exitosa' 
        WHERE id_caravana = v_id_car;
        RETURN 'Éxito';
    ELSE
        UPDATE sch_mercaderleyendas.caravana 
        SET estado_caravana = 'fallida' 
        WHERE id_caravana = v_id_car;
        DELETE FROM sch_mercaderleyendas.producto_caravana 
        WHERE id_caravana = v_id_car;
        RETURN 'Fracaso';
    END IF;
END;
$$ LANGUAGE plpgsql;


-- Mecánica 4: Producción semanal automática del producto inicial --

-- Se activa desde la base de datos mediante una tabla que simula el avance del tiempo --
-- Esta tabla y trigger permiten que al avanzar una semana simulada, se añadan 5 unidades del producto inicial --

CREATE TABLE avance_tiempo (
    id_avance SERIAL PRIMARY KEY,
    id_jugador INT REFERENCES jugador(id_jugador),
    semana_simulada INT,
    fecha_avance TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE OR REPLACE FUNCTION sch_mercaderleyendas.agregar_producto_semanal() RETURNS TRIGGER AS $$
BEGIN
    UPDATE sch_mercaderleyendas.inventario
    SET cantidad_productos = cantidad_productos + 5
    WHERE id_jugador = NEW.id_jugador
    AND id_producto = (
        SELECT id_producto 
        FROM sch_mercaderleyendas.producto_inicial 
        WHERE id_partida = (
            SELECT MAX(id_partida) 
            FROM sch_mercaderleyendas.partida 
            WHERE id_jugador = NEW.id_jugador
        )
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_agregar_producto_semanal
AFTER INSERT ON sch_mercaderleyendas.avance_tiempo
FOR EACH ROW
EXECUTE FUNCTION sch_mercaderleyendas.agregar_producto_semanal();


-- Mecánica 5: Registro automático en bitácora --

-- Triggers para registrar automáticamente en la bitácora acciones realizadas en las tablas clave --

CREATE OR REPLACE FUNCTION sch_mercaderleyendas.registrar_bitacora() 
RETURNS TRIGGER AS $$
DECLARE
    v_id_jugador INT;
    v_id_entidad INT;
    v_nombre_tabla TEXT := TG_TABLE_NAME;
    v_operacion TEXT := TG_OP;
BEGIN
    -- Distinguir si es DELETE (usar OLD) o INSERT/UPDATE (usar NEW)
    IF v_operacion = 'DELETE' THEN
        IF v_nombre_tabla = 'caravana' THEN
            SELECT p.id_jugador INTO v_id_jugador
            FROM sch_mercaderleyendas.personaje p
            JOIN sch_mercaderleyendas.ciudad c ON p.id_ciudad_actual = c.id_ciudad
            JOIN sch_mercaderleyendas.ruta r ON r.id_ciudad_origen = c.id_ciudad
            WHERE r.id_ruta = OLD.id_ruta
            LIMIT 1;
            v_id_entidad := OLD.id_caravana;

        ELSIF v_nombre_tabla = 'producto_caravana' THEN
            SELECT p.id_jugador INTO v_id_jugador
            FROM sch_mercaderleyendas.caravana ca
            JOIN sch_mercaderleyendas.ruta r ON ca.id_ruta = r.id_ruta
            JOIN sch_mercaderleyendas.ciudad c ON r.id_ciudad_origen = c.id_ciudad
            JOIN sch_mercaderleyendas.personaje p ON p.id_ciudad_actual = c.id_ciudad
            WHERE ca.id_caravana = OLD.id_caravana
            LIMIT 1;
            v_id_entidad := OLD.id_caravana;

        ELSE
            v_id_jugador := OLD.id_jugador;
            v_id_entidad := COALESCE(OLD.id_jugador, NULL);
        END IF;

    ELSE
        IF v_nombre_tabla = 'caravana' THEN
            SELECT p.id_jugador INTO v_id_jugador
            FROM sch_mercaderleyendas.personaje p
            JOIN sch_mercaderleyendas.ciudad c ON p.id_ciudad_actual = c.id_ciudad
            JOIN sch_mercaderleyendas.ruta r ON r.id_ciudad_origen = c.id_ciudad
            WHERE r.id_ruta = NEW.id_ruta
            LIMIT 1;
            v_id_entidad := NEW.id_caravana;

        ELSIF v_nombre_tabla = 'producto_caravana' THEN
            SELECT p.id_jugador INTO v_id_jugador
            FROM sch_mercaderleyendas.caravana ca
            JOIN sch_mercaderleyendas.ruta r ON ca.id_ruta = r.id_ruta
            JOIN sch_mercaderleyendas.ciudad c ON r.id_ciudad_origen = c.id_ciudad
            JOIN sch_mercaderleyendas.personaje p ON p.id_ciudad_actual = c.id_ciudad
            WHERE ca.id_caravana = NEW.id_caravana
            LIMIT 1;
            v_id_entidad := NEW.id_caravana;

        ELSE
            v_id_jugador := NEW.id_jugador;
            v_id_entidad := COALESCE(NEW.id_jugador, NULL);
        END IF;
    END IF;

    -- Insertar registro en bitácora
    INSERT INTO sch_mercaderleyendas.bitacora (
        id_jugador, 
        entidad_afectada, 
        id_entidad_afectada, 
        accion, 
        fecha
    )
    VALUES (
        v_id_jugador, 
        v_nombre_tabla, 
        v_id_entidad, 
        v_operacion, 
        CURRENT_TIMESTAMP
    );

    RETURN CASE WHEN v_operacion = 'DELETE' THEN OLD ELSE NEW END;
END;
$$ LANGUAGE plpgsql;



-- Trigger para tabla INVENTARIO
CREATE TRIGGER trigger_bitacora_inventario
AFTER INSERT OR UPDATE OR DELETE ON inventario
FOR EACH ROW
EXECUTE FUNCTION registrar_bitacora();

-- Trigger para tabla CARAVANA
CREATE TRIGGER trigger_bitacora_caravana
AFTER INSERT OR UPDATE OR DELETE ON caravana
FOR EACH ROW
EXECUTE FUNCTION registrar_bitacora();

-- Trigger para tabla JUGADOR_HABILIDAD
CREATE TRIGGER trigger_bitacora_jugador_habilidad
AFTER INSERT OR UPDATE OR DELETE ON jugador_habilidad
FOR EACH ROW
EXECUTE FUNCTION registrar_bitacora();

-- Trigger para tabla PRODUCTO_CARAVANA
CREATE TRIGGER trigger_bitacora_producto_caravana
AFTER INSERT OR UPDATE OR DELETE ON producto_caravana
FOR EACH ROW
EXECUTE FUNCTION registrar_bitacora();

-- Trigger para tabla TRANSACCION
CREATE TRIGGER trigger_bitacora_transaccion
AFTER INSERT OR UPDATE OR DELETE ON transaccion
FOR EACH ROW
EXECUTE FUNCTION registrar_bitacora();

-- Trigger para tabla PARTIDA
CREATE TRIGGER trigger_bitacora_partida
AFTER INSERT OR UPDATE OR DELETE ON partida
FOR EACH ROW
EXECUTE FUNCTION registrar_bitacora();

-- Trigger para tabla VIAJE
CREATE TRIGGER trigger_bitacora_viaje
AFTER INSERT OR UPDATE OR DELETE ON viaje
FOR EACH ROW
EXECUTE FUNCTION registrar_bitacora();

-- Trigger para tabla AVANCE_TIEMPO
CREATE TRIGGER trigger_bitacora_avance_tiempo
AFTER INSERT OR UPDATE OR DELETE ON avance_tiempo
FOR EACH ROW
EXECUTE FUNCTION registrar_bitacora();



-- Mecánica 6: Desbloqueo automático de habilidades tras cumplir condiciones --

-- Función que evalúa si un jugador ha hecho al menos 5 ventas y, si es así, desbloquea una habilidad --

-- Mecánica 6: Desbloqueo automático de habilidades tras cumplir condiciones --

-- Función que evalúa si un jugador ha hecho al menos 5 ventas y, si es así, desbloquea una habilidad --

CREATE OR REPLACE FUNCTION sch_mercaderleyendas.evaluar_desbloqueo_habilidad(
    p_id_jugador INT, 
    p_id_personaje INT
) RETURNS VOID AS $$
DECLARE
    ventas INT;
    compras INT;
    misiones INT;
    viajes_mar INT;
    ataques_superados INT;
    rutas_descubiertas INT;
    tormentas_superadas INT;
    habilidad_id INT;
    personaje_actual TEXT;
BEGIN
    -- Obtener el nombre del personaje actual
    SELECT nombre_personaje INTO personaje_actual
    FROM sch_mercaderleyendas.personaje
    WHERE id_personaje = p_id_personaje;

    -- HABILIDADES GENERALES

    -- Comercio Avanzado → 10 ventas exitosas
    SELECT COUNT(*) INTO ventas
    FROM sch_mercaderleyendas.transaccion
    WHERE id_jugador = p_id_jugador
      AND tipo_transaccion = 'venta';

    IF ventas >= 10 THEN
        SELECT id_habilidad INTO habilidad_id
        FROM sch_mercaderleyendas.habilidad
        WHERE nombre_habilidad = 'Comercio Avanzado';

        UPDATE sch_mercaderleyendas.jugador_habilidad
        SET estado_habilidad = 'activa', fecha_desbloqueo = CURRENT_DATE
        WHERE id_personaje = p_id_personaje
          AND id_habilidad = habilidad_id
          AND estado_habilidad = 'inactiva';
    END IF;

    -- Liderazgo → 5 misiones completadas
	SELECT COUNT(*) INTO misiones
	FROM sch_mercaderleyendas.viaje v
	JOIN sch_mercaderleyendas.caravana c ON v.id_caravana = c.id_caravana
	WHERE c.id_personaje = p_id_personaje;
	
	IF misiones >= 5 THEN
	    SELECT id_habilidad INTO habilidad_id
	    FROM sch_mercaderleyendas.habilidad
	    WHERE nombre_habilidad = 'Liderazgo';
	
	    UPDATE sch_mercaderleyendas.jugador_habilidad
	    SET estado_habilidad = 'activa', fecha_desbloqueo = CURRENT_DATE
	    WHERE id_personaje = p_id_personaje
	      AND id_habilidad = habilidad_id
	      AND estado_habilidad = 'inactiva';
	END IF;

    -- Conocimientos de Rutas Secretas → 3 rutas descubiertas
    SELECT COUNT(*) INTO rutas_descubiertas
    FROM sch_mercaderleyendas.ruta
    WHERE descubierta_por = p_id_personaje;

    IF rutas_descubiertas >= 3 THEN
        SELECT id_habilidad INTO habilidad_id
        FROM sch_mercaderleyendas.habilidad
        WHERE nombre_habilidad = 'Conocimientos de Rutas Secretas';

        UPDATE sch_mercaderleyendas.jugador_habilidad
        SET estado_habilidad = 'activa', fecha_desbloqueo = CURRENT_DATE
        WHERE id_personaje = p_id_personaje
          AND id_habilidad = habilidad_id
          AND estado_habilidad = 'inactiva';
    END IF;

    -- Navegación de Tormentas → sobrevivir 3 tormentas
    SELECT COUNT(*) INTO tormentas_superadas
    FROM sch_mercaderleyendas.eventos_mar
    WHERE id_personaje = p_id_personaje
      AND tipo_evento = 'tormenta'
      AND resultado_evento = 'superado';

    IF tormentas_superadas >= 3 THEN
        SELECT id_habilidad INTO habilidad_id
        FROM sch_mercaderleyendas.habilidad
        WHERE nombre_habilidad = 'Navegación de Tormentas';

        UPDATE sch_mercaderleyendas.jugador_habilidad
        SET estado_habilidad = 'activa', fecha_desbloqueo = CURRENT_DATE
        WHERE id_personaje = p_id_personaje
          AND id_habilidad = habilidad_id
          AND estado_habilidad = 'inactiva';
    END IF;

    -- HABILIDADES ESPECÍFICAS DE KIRAN
    IF personaje_actual = 'Kiran' THEN

        -- Negociación Avanzada
        SELECT COUNT(*) INTO ventas
        FROM sch_mercaderleyendas.transaccion
        WHERE id_jugador = p_id_jugador
          AND tipo_transaccion = 'venta'
          AND precio_unitario >= 50;

        IF ventas >= 3 THEN
            SELECT id_habilidad INTO habilidad_id
            FROM sch_mercaderleyendas.habilidad
            WHERE nombre_habilidad = 'Negociación Avanzada'
              AND personaje_asociado = 'Kiran';

            UPDATE sch_mercaderleyendas.jugador_habilidad
            SET estado_habilidad = 'activa', fecha_desbloqueo = CURRENT_DATE
            WHERE id_personaje = p_id_personaje
              AND id_habilidad = habilidad_id
              AND estado_habilidad = 'inactiva';
        END IF;

        -- Red de Contactos
        SELECT COUNT(DISTINCT t.id_ciudad) INTO ventas
        FROM sch_mercaderleyendas.transaccion t
        WHERE t.id_jugador = p_id_jugador
          AND t.tipo_transaccion = 'venta';

        IF ventas >= 3 THEN
            SELECT id_habilidad INTO habilidad_id
            FROM sch_mercaderleyendas.habilidad
            WHERE nombre_habilidad = 'Red de Contactos'
              AND personaje_asociado = 'Kiran';

            UPDATE sch_mercaderleyendas.jugador_habilidad
            SET estado_habilidad = 'activa', fecha_desbloqueo = CURRENT_DATE
            WHERE id_personaje = p_id_personaje
              AND id_habilidad = habilidad_id
              AND estado_habilidad = 'inactiva';
        END IF;

        -- Inversión Inteligente
        SELECT COUNT(*) INTO compras
        FROM sch_mercaderleyendas.transaccion
        WHERE id_jugador = p_id_jugador
          AND tipo_transaccion = 'compra'
          AND precio_unitario <= 10;

        IF ventas >= 5 AND compras >= 5 THEN
            SELECT id_habilidad INTO habilidad_id
            FROM sch_mercaderleyendas.habilidad
            WHERE nombre_habilidad = 'Inversión Inteligente'
              AND personaje_asociado = 'Kiran';

            UPDATE sch_mercaderleyendas.jugador_habilidad
            SET estado_habilidad = 'activa', fecha_desbloqueo = CURRENT_DATE
            WHERE id_personaje = p_id_personaje
              AND id_habilidad = habilidad_id
              AND estado_habilidad = 'inactiva';
        END IF;

        -- Análisis de Mercado
        SELECT COUNT(*) INTO misiones
        FROM sch_mercaderleyendas.transaccion
        WHERE id_jugador = p_id_jugador;

        IF misiones >= 5 THEN
            SELECT id_habilidad INTO habilidad_id
            FROM sch_mercaderleyendas.habilidad
            WHERE nombre_habilidad = 'Análisis de Mercado'
              AND personaje_asociado = 'Kiran';

            UPDATE sch_mercaderleyendas.jugador_habilidad
            SET estado_habilidad = 'activa', fecha_desbloqueo = CURRENT_DATE
            WHERE id_personaje = p_id_personaje
              AND id_habilidad = habilidad_id
              AND estado_habilidad = 'inactiva';
        END IF;
    END IF;

    -- HABILIDADES ESPECÍFICAS DE LEENA
    IF personaje_actual = 'Leena' THEN

        -- Maestría en Navegación
        SELECT COUNT(*) INTO viajes_mar
        FROM sch_mercaderleyendas.viaje
        WHERE id_personaje = p_id_personaje
          AND tipo_viaje = 'mar'
          AND accidentes = 0;

        IF viajes_mar >= 10 THEN
            SELECT id_habilidad INTO habilidad_id
            FROM sch_mercaderleyendas.habilidad
            WHERE nombre_habilidad = 'Maestría en Navegación'
              AND personaje_asociado = 'Leena';

            UPDATE sch_mercaderleyendas.jugador_habilidad
            SET estado_habilidad = 'activa', fecha_desbloqueo = CURRENT_DATE
            WHERE id_personaje = p_id_personaje
              AND id_habilidad = habilidad_id
              AND estado_habilidad = 'inactiva';
        END IF;

        -- Defensa Costera
        SELECT COUNT(*) INTO ataques_superados
        FROM sch_mercaderleyendas.eventos_mar
        WHERE id_personaje = p_id_personaje
          AND tipo_evento = 'ataque pirata'
          AND resultado_evento = 'superado';

        IF ataques_superados >= 3 THEN
            SELECT id_habilidad INTO habilidad_id
            FROM sch_mercaderleyendas.habilidad
            WHERE nombre_habilidad = 'Defensa Costera'
              AND personaje_asociado = 'Leena';

            UPDATE sch_mercaderleyendas.jugador_habilidad
            SET estado_habilidad = 'activa', fecha_desbloqueo = CURRENT_DATE
            WHERE id_personaje = p_id_personaje
              AND id_habilidad = habilidad_id
              AND estado_habilidad = 'inactiva';
        END IF;

        -- etc. (seguirías completando tus habilidades específicas de Leena igual)
    END IF;

END;
$$ LANGUAGE plpgsql;



-- Mecánica 7: Actualización automática del inventario luego de una compra o venta --

-- Función que actualiza el inventario automáticamente después de una compra o venta --

CREATE OR REPLACE FUNCTION actualizar_inventario() RETURNS TRIGGER AS $$
DECLARE
    cantidad_actual INT;
BEGIN
    IF NEW.tipo_transaccion = 'venta' THEN
        -- Verificar si el producto está en inventario y tiene suficiente cantidad
        SELECT cantidad_productos INTO cantidad_actual
        FROM inventario
        WHERE id_jugador = NEW.id_jugador AND id_producto = NEW.id_producto;

        IF cantidad_actual IS NULL THEN
            RAISE EXCEPTION 'No se puede vender un producto que no está en el inventario.';
        ELSIF cantidad_actual < NEW.cantidad_productos_transaccion THEN
            RAISE EXCEPTION 'Inventario insuficiente para completar la venta.';
        END IF;

        -- Descontar la cantidad vendida
        UPDATE inventario
        SET cantidad_productos = cantidad_productos - NEW.cantidad_productos_transaccion
        WHERE id_jugador = NEW.id_jugador AND id_producto = NEW.id_producto;

    ELSIF NEW.tipo_transaccion = 'compra' THEN
        -- Verificar si ya existe el producto en el inventario
        SELECT cantidad_productos INTO cantidad_actual
        FROM inventario
        WHERE id_jugador = NEW.id_jugador AND id_producto = NEW.id_producto;

        IF cantidad_actual IS NULL THEN
            -- Crear el registro si no existe
            INSERT INTO inventario (id_jugador, id_producto, cantidad_productos)
            VALUES (NEW.id_jugador, NEW.id_producto, NEW.cantidad_productos_transaccion);
        ELSE
            -- Sumar al inventario existente
            UPDATE inventario
            SET cantidad_productos = cantidad_productos + NEW.cantidad_productos_transaccion
            WHERE id_jugador = NEW.id_jugador AND id_producto = NEW.id_producto;
        END IF;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;



-- Mecánica 8: Validación de que el producto pueda venderse solo en ciudades que lo producen --

-- Función que impide registrar una venta si el producto no está producido en esa ciudad o si no se transportó en la caravana--

CREATE OR REPLACE FUNCTION validar_venta_en_ciudad() RETURNS TRIGGER AS $$
BEGIN
    -- Caso 1: el producto es producido en la ciudad
    IF EXISTS (
        SELECT 1 FROM ciudad_produce_producto
        WHERE id_ciudad = NEW.id_ciudad
        AND id_producto = NEW.id_producto
    ) THEN
        RETURN NEW;
    END IF;

    -- Caso 2: el producto fue transportado por una caravana con viaje finalizado a esta ciudad
    IF EXISTS (
        SELECT 1
        FROM producto_caravana pc
        JOIN viaje v ON pc.id_caravana = v.id_caravana
        JOIN caravana c ON c.id_caravana = pc.id_caravana
        JOIN ruta r ON c.id_ruta = r.id_ruta
        WHERE pc.id_producto = NEW.id_producto
        AND v.id_caravana = pc.id_caravana
        AND r.id_ciudad_destino = NEW.id_ciudad
        -- opcional: AND v.estado = 'finalizado' si se modela así
    ) THEN
        RETURN NEW;
    END IF;

    -- Si no se cumple ninguna condición, lanzar error
    RAISE EXCEPTION 'No se puede vender el producto: no se produce ni fue transportado a esta ciudad.';
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_validar_venta
BEFORE INSERT ON transaccion
FOR EACH ROW
EXECUTE FUNCTION validar_venta_en_ciudad();
