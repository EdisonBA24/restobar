-- TABLAS PARA EL PROYECTO --

CREATE TABLE unidades_medida (
    id INT IDENTITY(1,1) PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL,
    abreviatura VARCHAR(10) NOT NULL,
    activo BIT DEFAULT 1
);

insert into unidades_medida (nombre, abreviatura)
select 'Unidad','Und'
union 
select 'Gramos','Gr'
union 
select 'Kilogramos','Kg'


CREATE TABLE productos (
    id INT IDENTITY(1,1) PRIMARY KEY,

    nombre VARCHAR(150) NOT NULL,
    codigo VARCHAR(50),
    categoria VARCHAR(100),

    unidad_id INT,
    tipo VARCHAR(20) NOT NULL, -- INSUMO / RECETA

    precio_compra DECIMAL(12,2) DEFAULT 0,
    precio_venta DECIMAL(12,2) DEFAULT 0,
    costo DECIMAL(12,2) DEFAULT 0,
    margen DECIMAL(5,2) DEFAULT 0,

    stock DECIMAL(12,2) DEFAULT 0,

    activo BIT DEFAULT 1,
    fecha_creacion DATETIME DEFAULT GETDATE(),

    CONSTRAINT fk_producto_unidad FOREIGN KEY (unidad_id)
    REFERENCES unidades_medida(id)
);


CREATE TABLE recetas (
    id INT IDENTITY(1,1) PRIMARY KEY,
    producto_id INT NOT NULL,
    activo BIT DEFAULT 1,

    CONSTRAINT fk_receta_producto FOREIGN KEY (producto_id)
    REFERENCES productos(id)
);


CREATE TABLE recetas_detalle (
    id INT IDENTITY(1,1) PRIMARY KEY,

    receta_id INT NOT NULL,
    insumo_id INT NOT NULL,
    cantidad DECIMAL(12,4) NOT NULL,

    CONSTRAINT fk_receta_detalle_receta FOREIGN KEY (receta_id)
    REFERENCES recetas(id),

    CONSTRAINT fk_receta_detalle_insumo FOREIGN KEY (insumo_id)
    REFERENCES productos(id)
);


CREATE TABLE compras (
    id INT IDENTITY(1,1) PRIMARY KEY,

    proveedor VARCHAR(150),
    fecha DATETIME DEFAULT GETDATE(),
    total DECIMAL(12,2) DEFAULT 0
);


CREATE TABLE detalle_compras (
    id INT IDENTITY(1,1) PRIMARY KEY,

    compra_id INT NOT NULL,
    producto_id INT NOT NULL,
    cantidad DECIMAL(12,2),
    precio DECIMAL(12,2),

    CONSTRAINT fk_detalle_compra FOREIGN KEY (compra_id)
    REFERENCES compras(id),

    CONSTRAINT fk_detalle_producto FOREIGN KEY (producto_id)
    REFERENCES productos(id)
);


CREATE TABLE ventas (
    id INT IDENTITY(1,1) PRIMARY KEY,

    cliente VARCHAR(150),
    fecha DATETIME DEFAULT GETDATE(),
    total DECIMAL(12,2),

    metodo_pago VARCHAR(50),
    usuario VARCHAR(50)
);


CREATE TABLE detalle_ventas (
    id INT IDENTITY(1,1) PRIMARY KEY,

    venta_id INT NOT NULL,
    producto_id INT NOT NULL,
    cantidad DECIMAL(12,2),
    precio DECIMAL(12,2),

    CONSTRAINT fk_detalle_venta FOREIGN KEY (venta_id)
    REFERENCES ventas(id),

    CONSTRAINT fk_detalle_venta_producto FOREIGN KEY (producto_id)
    REFERENCES productos(id)
);
