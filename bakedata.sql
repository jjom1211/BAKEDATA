SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0;
SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0;
SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION';

-- -----------------------------------------------------
-- Schema mydb
-- -----------------------------------------------------
DROP SCHEMA IF EXISTS `mydb` ;

-- -----------------------------------------------------
-- Schema mydb
-- -----------------------------------------------------
CREATE SCHEMA IF NOT EXISTS `mydb` DEFAULT CHARACTER SET utf8 ;
-- -----------------------------------------------------
-- Schema new_schema1
-- -----------------------------------------------------
USE `mydb` ;

-- -----------------------------------------------------
-- Table `mydb`.`table1`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `mydb`.`table1` ;

CREATE TABLE IF NOT EXISTS `mydb`.`table1` (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL
)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `mydb`.`usuarios`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `mydb`.`usuarios` ;

CREATE TABLE IF NOT EXISTS `mydb`.`usuarios` (
  `usu_id` DECIMAL(10,0) NOT NULL,
  `usu_nombre` VARCHAR(50) NOT NULL,
  `usu_apellido` VARCHAR(50) NOT NULL,
  `usu_correo` VARCHAR(45) NOT NULL,
  `usu_contrasenia` VARCHAR(45) NOT NULL,
  `usu_telefono` VARCHAR(10) NOT NULL,
  PRIMARY KEY (`usu_id`),
  UNIQUE INDEX `usu_correo_UNIQUE` (`usu_correo` ASC) VISIBLE)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `mydb`.`proveedores`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `mydb`.`proveedores` ;

CREATE TABLE IF NOT EXISTS `mydb`.`proveedores` (
  `prov_id` DECIMAL(6,0) NOT NULL,
  `prov_nombre_empresa` VARCHAR(100) NULL,
  `prov_nombre` VARCHAR(50) NULL,
  `prov_apellido` VARCHAR(45) NULL,
  `prov_correo` VARCHAR(45) NOT NULL,
  `prov_telefono` VARCHAR(10) NOT NULL,
  `prov_estado` CHAR(1) NOT NULL,
  PRIMARY KEY (`prov_id`),
  UNIQUE INDEX `prov_correo_UNIQUE` (`prov_correo` ASC) VISIBLE,
  UNIQUE INDEX `prov_telefono_UNIQUE` (`prov_telefono` ASC) VISIBLE)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `mydb`.`unidad_medida`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `mydb`.`unidad_medida` ;

CREATE TABLE IF NOT EXISTS `mydb`.`unidad_medida` (
  `unimed` CHAR(4) NOT NULL,
  `unimed_extendido` VARCHAR(20) NOT NULL,
  PRIMARY KEY (`unimed`))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `mydb`.`materias_primas`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `mydb`.`materias_primas` ;

CREATE TABLE IF NOT EXISTS `mydb`.`materias_primas` (
  `matprim_id` DECIMAL(6,0) NOT NULL,
  `matprim_nombre` VARCHAR(50) NOT NULL,
  `matprim_unimed` CHAR(4) NOT NULL,
  `matprim_descr` VARCHAR(100) NULL,
  PRIMARY KEY (`matprim_id`),
  INDEX `fk_materias_primas_unidad_medida1_idx` (`matprim_unimed` ASC) VISIBLE,
  CONSTRAINT `fk_materias_primas_unidad_medida`
    FOREIGN KEY (`matprim_unimed`)
    REFERENCES `mydb`.`unidad_medida` (`unimed`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `mydb`.`productos`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `mydb`.`productos` ;

CREATE TABLE IF NOT EXISTS `mydb`.`productos` (
  `pro_id` DECIMAL(6,0) NOT NULL,
  `pro_nombre` VARCHAR(50) NOT NULL,
  `pro_precio` DECIMAL(6,2) NOT NULL,
  `pro_costo_unit` DECIMAL(6,2) NOT NULL,
  `pro_unimed` CHAR(4) NOT NULL,
  `pro_descr` VARCHAR(100) NULL,
  PRIMARY KEY (`pro_id`),
  INDEX `fk_productos_unidad_medida_idx` (`pro_unimed` ASC) VISIBLE,
  CONSTRAINT `fk_productos_unidad_medida`
    FOREIGN KEY (`pro_unimed`)
    REFERENCES `mydb`.`unidad_medida` (`unimed`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `mydb`.`sucursales`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `mydb`.`sucursales` ;

CREATE TABLE IF NOT EXISTS `mydb`.`sucursales` (
  `suc_id` INT NOT NULL,
  `suc_nombre` VARCHAR(45) NOT NULL,
  `suc_direccion` VARCHAR(300) NOT NULL,
  `suc_correo` VARCHAR(45) NOT NULL,
  `suc_telefono` VARCHAR(10) NULL,
  PRIMARY KEY (`suc_id`),
  UNIQUE INDEX `suc_correo_UNIQUE` (`suc_correo` ASC) VISIBLE)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `mydb`.`inventario_materias_primas`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `mydb`.`inventario_materias_primas` ;

CREATE TABLE IF NOT EXISTS `mydb`.`inventario_materias_primas` (
  `invmatprim_matprim_fk` DECIMAL(6,0) NOT NULL,
  `invmatprim_suc_fk` INT NOT NULL,
  `invmatprim_matprim_nombre` VARCHAR(50) NOT NULL,
  `invmatprim_unimed` CHAR(4) NOT NULL,
  `invmatprim_stock` DECIMAL(12,2) NOT NULL,
  INDEX `fk_inventario_materias_primas_sucursales_idx` (`invmatprim_suc_fk` ASC) VISIBLE,
  PRIMARY KEY (`invmatprim_matprim_fk`, `invmatprim_suc_fk`),
  INDEX `fk_inventario_materias_primas_unidad_medida_idx` (`invmatprim_unimed` ASC) VISIBLE,
  CONSTRAINT `fk_inventario_materias_primas_materias_primas`
    FOREIGN KEY (`invmatprim_matprim_fk`)
    REFERENCES `mydb`.`materias_primas` (`matprim_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_inventario_materias_primas_sucursales1`
    FOREIGN KEY (`invmatprim_suc_fk`)
    REFERENCES `mydb`.`sucursales` (`suc_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_inventario_materias_primas_unidad_medida1`
    FOREIGN KEY (`invmatprim_unimed`)
    REFERENCES `mydb`.`unidad_medida` (`unimed`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `mydb`.`inventario_productos`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `mydb`.`inventario_productos` ;

CREATE TABLE IF NOT EXISTS `mydb`.`inventario_productos` (
  `invpro_pro_fk` DECIMAL(6,0) NOT NULL,
  `invpro_suc_fk` INT NOT NULL,
  `pro_nombre` VARCHAR(50) NOT NULL,
  `pro_stock` DECIMAL(12,2) NOT NULL,
  INDEX `fk_inventario_productos_sucursales_idx` (`invpro_suc_fk` ASC) VISIBLE,
  PRIMARY KEY (`invpro_pro_fk`, `invpro_suc_fk`),
  CONSTRAINT `fk_inventario_productos_productos1`
    FOREIGN KEY (`invpro_pro_fk`)
    REFERENCES `mydb`.`productos` (`pro_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_inventario_productos_sucursales1`
    FOREIGN KEY (`invpro_suc_fk`)
    REFERENCES `mydb`.`sucursales` (`suc_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `mydb`.`empleados`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `mydb`.`empleados` ;

CREATE TABLE IF NOT EXISTS `mydb`.`empleados` (
  `emp_id` DECIMAL(6,0) NOT NULL,
  `emp_nombre` VARCHAR(50) NOT NULL,
  `emp_apellido` VARCHAR(60) NOT NULL,
  `emp_contrat` DATE NOT NULL,
  `emp_correo` VARCHAR(50) NOT NULL,
  `emp_contrasenia` VARCHAR(50) NOT NULL,
  `emp_telefono` VARCHAR(13) NOT NULL,
  PRIMARY KEY (`emp_id`),
  UNIQUE INDEX `emp_correo_UNIQUE` (`emp_correo` ASC) VISIBLE,
  UNIQUE INDEX `emp_telefono_UNIQUE` (`emp_telefono` ASC) VISIBLE)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `mydb`.`pedidos_productos`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `mydb`.`pedidos_productos` ;

CREATE TABLE IF NOT EXISTS `mydb`.`pedidos_productos` (
  `pedpro_id` DECIMAL(20,0) NOT NULL,
  `pedpro_suc_fk` INT NOT NULL,
  `pedpro_usu_fk` DECIMAL(10,0) NOT NULL,
  `pedpro_fecha` DATE NOT NULL,
  `pedpro_monto_total` DECIMAL(20,2) NOT NULL,
  `pedpro_asunto` VARCHAR(45) NOT NULL,
  `pedpro_comentarios` VARCHAR(200) NULL,
  PRIMARY KEY (`pedpro_id`, `pedpro_suc_fk`),
  INDEX `fk_pedidos_usuarios_idx` (`pedpro_usu_fk` ASC) VISIBLE,
  INDEX `fk_pedidos_productos_sucursales_idx` (`pedpro_suc_fk` ASC) VISIBLE,
  CONSTRAINT `fk_pedidos_usuarios`
    FOREIGN KEY (`pedpro_usu_fk`)
    REFERENCES `mydb`.`usuarios` (`usu_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_pedidos_productos_sucursales`
    FOREIGN KEY (`pedpro_suc_fk`)
    REFERENCES `mydb`.`sucursales` (`suc_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `mydb`.`pedidos_productos_extendidos`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `mydb`.`pedidos_productos_extendidos` ;

CREATE TABLE IF NOT EXISTS `mydb`.`pedidos_productos_extendidos` (
  `pedproex_pedpro_fk` DECIMAL(20,0) NOT NULL,
  `pedproex_suc_fk` INT NOT NULL,
  `pedproex_pro_fk` DECIMAL(6,0) NOT NULL,
  `pro_nombre` VARCHAR(50) NOT NULL,
  `pro_cant` INT NOT NULL,
  `pro_precio_unit` DECIMAL(6,2) NOT NULL,
  `pro_precio_total` DECIMAL(20,2) NOT NULL,
  INDEX `fk_pedido_extendido_productos_idx` (`pedproex_pro_fk` ASC) VISIBLE,
  INDEX `fk_pedido_extendido_pedidos_productos_idx` (`pedproex_pedpro_fk` ASC, `pedproex_suc_fk` ASC) VISIBLE,
  CONSTRAINT `fk_pedido_extendido_productos1`
    FOREIGN KEY (`pedproex_pro_fk`)
    REFERENCES `mydb`.`productos` (`pro_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_pedido_extendido_pedidos_productos1`
    FOREIGN KEY (`pedproex_pedpro_fk` , `pedproex_suc_fk`)
    REFERENCES `mydb`.`pedidos_productos` (`pedpro_id` , `pedpro_suc_fk`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `mydb`.`pedido_materia_prima`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `mydb`.`pedido_materia_prima` ;

CREATE TABLE IF NOT EXISTS `mydb`.`pedido_materia_prima` (
  `pedmatprim_id` DECIMAL(20,0) NOT NULL,
  `pedmatprim_prov_fk` DECIMAL(6,0) NOT NULL,
  `pedmatprim_suc_fk` INT NOT NULL,
  `pedmatprim_fecha` DATE NOT NULL,
  `pedmatprim_monto_total` DECIMAL(20,2) NOT NULL,
  `pedmatprim_prov_nombre_empresa` VARCHAR(100) NULL,
  PRIMARY KEY (`pedmatprim_id`),
  INDEX `fk_pedido_materia_prima_proveedores_idx` (`pedmatprim_prov_fk` ASC) VISIBLE,
  INDEX `fk_pedido_materia_prima_sucursales_idx` (`pedmatprim_suc_fk` ASC) VISIBLE,
  CONSTRAINT `fk_pedido_materia_prima_proveedores`
    FOREIGN KEY (`pedmatprim_prov_fk`)
    REFERENCES `mydb`.`proveedores` (`prov_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_pedido_materia_prima_sucursales1`
    FOREIGN KEY (`pedmatprim_suc_fk`)
    REFERENCES `mydb`.`sucursales` (`suc_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `mydb`.`pedidos_materias_primas_extendidos`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `mydb`.`pedidos_materias_primas_extendidos` ;

CREATE TABLE IF NOT EXISTS `mydb`.`pedidos_materias_primas_extendidos` (
  `pedmatprimex_matprim_fk` DECIMAL(6,0) NOT NULL,
  `pedmatprimex_pedmatprim_fk` DECIMAL(20,0) NOT NULL,
  `pedmatprimex_unimed` CHAR(4) NOT NULL,
  `matprim_nombre` VARCHAR(50) NOT NULL,
  `matprim_cant` INT NOT NULL,
  `matprim_costo_unit` DECIMAL(6,2) NOT NULL,
  `matprim_costo_total` DECIMAL(20,2) NOT NULL,
  INDEX `fk_pedidos_materias_primas_extendidos_materias_primas_idx` (`pedmatprimex_matprim_fk` ASC) VISIBLE,
  INDEX `fk_pedidos_materias_primas_extendidos_pedido_materia_prima_idx` (`pedmatprimex_pedmatprim_fk` ASC) VISIBLE,
  INDEX `fk_pedidos_materias_primas_extendidos_unidad_medida_idx` (`pedmatprimex_unimed` ASC) VISIBLE,
  CONSTRAINT `fk_pedidos_materias_primas_extendidos_materias_primas`
    FOREIGN KEY (`pedmatprimex_matprim_fk`)
    REFERENCES `mydb`.`materias_primas` (`matprim_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_pedidos_materias_primas_extendidos_pedido_materia_prima`
    FOREIGN KEY (`pedmatprimex_pedmatprim_fk`)
    REFERENCES `mydb`.`pedido_materia_prima` (`pedmatprim_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_pedidos_materias_primas_extendidos_unidad_medida`
    FOREIGN KEY (`pedmatprimex_unimed`)
    REFERENCES `mydb`.`unidad_medida` (`unimed`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `mydb`.`roles_empleados`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `mydb`.`roles_empleados` ;

CREATE TABLE IF NOT EXISTS `mydb`.`roles_empleados` (
  `rolemp` VARCHAR(20) NOT NULL,
  `rolemp_emp_fk` DECIMAL(6,0) NOT NULL,
  INDEX `fk_roles_empleados_empleados_idx` (`rolemp_emp_fk` ASC) VISIBLE,
  CONSTRAINT `fk_roles_empleados_empleados`
    FOREIGN KEY (`rolemp_emp_fk`)
    REFERENCES `mydb`.`empleados` (`emp_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `mydb`.`caja`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `mydb`.`caja` ;

CREATE TABLE IF NOT EXISTS `mydb`.`caja` (
  `caja_id` INT NOT NULL,
  `caja_suc_fk` INT NOT NULL,
  `caja_efectivo` DECIMAL(10,2) NOT NULL,
  `caja_total_dia` DECIMAL(10,2) NOT NULL,
  PRIMARY KEY (`caja_id`, `caja_suc_fk`),
  INDEX `fk_caja_sucursales_idx` (`caja_suc_fk` ASC) VISIBLE,
  CONSTRAINT `fk_caja_sucursales1`
    FOREIGN KEY (`caja_suc_fk`)
    REFERENCES `mydb`.`sucursales` (`suc_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `mydb`.`venta`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `mydb`.`venta` ;

CREATE TABLE IF NOT EXISTS `mydb`.`venta` (
  `venta_emp_fk` DECIMAL(6,0) NOT NULL,
  `venta_caja_fk` INT NOT NULL,
  `venta_suc_fk` INT NOT NULL,
  `venta_fecha` DATE NOT NULL,
  `venta_monto_total` DECIMAL(12,2) NOT NULL,
  `venta_sucursal` VARCHAR(45) NOT NULL,
  INDEX `fk_venta_caja_idx` (`venta_caja_fk` ASC, `venta_suc_fk` ASC) VISIBLE,
  PRIMARY KEY (`venta_caja_fk`, `venta_suc_fk`, `venta_emp_fk`),
  INDEX `fk_venta_empleados_idx` (`venta_emp_fk` ASC) VISIBLE,
  CONSTRAINT `fk_venta_caja`
    FOREIGN KEY (`venta_caja_fk` , `venta_suc_fk`)
    REFERENCES `mydb`.`caja` (`caja_id` , `caja_suc_fk`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_venta_empleados`
    FOREIGN KEY (`venta_emp_fk`)
    REFERENCES `mydb`.`empleados` (`emp_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `mydb`.`detalles_venta`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `mydb`.`detalles_venta` ;

CREATE TABLE IF NOT EXISTS `mydb`.`detalles_venta` (
  `detven_emp_fk` DECIMAL(6,0) NOT NULL,
  `detven_caja_fk` INT NOT NULL,
  `detven_caja_suc_fk` INT NOT NULL,
  `detven_pro_fk` DECIMAL(6,0) NOT NULL,
  `detven_pro_precio` DECIMAL(6,2) NOT NULL,
  `detven_pro_nombre` VARCHAR(50) NOT NULL,
  `detven_pro_cant` INT NOT NULL,
  `detven_pro_precio_total` VARCHAR(45) NOT NULL,
  INDEX `fk_detalles_venta_venta_idx` (`detven_emp_fk` ASC, `detven_caja_fk` ASC, `detven_caja_suc_fk` ASC) VISIBLE,
  PRIMARY KEY (`detven_emp_fk`, `detven_caja_fk`, `detven_caja_suc_fk`),
  INDEX `fk_detalles_venta_productos_idx` (`detven_pro_fk` ASC) VISIBLE,
  CONSTRAINT `fk_detalles_venta_venta1`
    FOREIGN KEY (`detven_caja_fk` , `detven_caja_suc_fk`)
    REFERENCES `mydb`.`venta` (`venta_caja_fk` , `venta_suc_fk`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_detalles_venta_productos`
    FOREIGN KEY (`detven_pro_fk`)
    REFERENCES `mydb`.`productos` (`pro_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `mydb`.`limpieza`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `mydb`.`limpieza` ;

CREATE TABLE IF NOT EXISTS `mydb`.`limpieza` (
  `lim_id` INT NOT NULL,
  `lim_actividad` VARCHAR(200) NOT NULL,
  PRIMARY KEY (`lim_id`))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `mydb`.`limpieza_calendario`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `mydb`.`limpieza_calendario` ;

CREATE TABLE IF NOT EXISTS `mydb`.`limpieza_calendario` (
  `limcal_fecha` DATETIME NOT NULL,
  `limcal_estado` CHAR(1) NOT NULL,
  PRIMARY KEY (`limcal_fecha`))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `mydb`.`limpieza_dia`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `mydb`.`limpieza_dia` ;

CREATE TABLE IF NOT EXISTS `mydb`.`limpieza_dia` (
  `limdia_limcal_fecha` DATETIME NOT NULL,
  `limdia_lim_fk` INT NOT NULL,
  `limdia_act_estado` CHAR(1) NOT NULL,
  INDEX `fk_limpieza_dia_limpieza_idx` (`limdia_lim_fk` ASC) VISIBLE,
  INDEX `fk_limpieza_dia_limpieza_calendario1_idx` (`limdia_limcal_fecha` ASC) VISIBLE,
  CONSTRAINT `fk_limpieza_dia_limpieza`
    FOREIGN KEY (`limdia_lim_fk`)
    REFERENCES `mydb`.`limpieza` (`lim_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_limpieza_dia_limpieza_calendario`
    FOREIGN KEY (`limdia_limcal_fecha`)
    REFERENCES `mydb`.`limpieza_calendario` (`limcal_fecha`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `mydb`.`reparto_calendario`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `mydb`.`reparto_calendario` ;

CREATE TABLE IF NOT EXISTS `mydb`.`reparto_calendario` (
  `repcal_fecha` DATETIME NOT NULL,
  `repcal_pedpro_fk` DECIMAL(20,0) NOT NULL,
  `repcal_suc_fk` INT NOT NULL,
  `repcal_estado` CHAR(1) NOT NULL,
  PRIMARY KEY (`repcal_fecha`, `repcal_pedpro_fk`, `repcal_suc_fk`),
  INDEX `fk_reparto_calendario_pedidos_productos1_idx` (`repcal_pedpro_fk` ASC, `repcal_suc_fk` ASC) VISIBLE,
  CONSTRAINT `fk_reparto_calendario_pedidos_productos`
    FOREIGN KEY (`repcal_pedpro_fk` , `repcal_suc_fk`)
    REFERENCES `mydb`.`pedidos_productos` (`pedpro_id` , `pedpro_suc_fk`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `mydb`.`entrega_dia`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `mydb`.`entrega_dia` ;

CREATE TABLE IF NOT EXISTS `mydb`.`entrega_dia` (
  `entdia_repcal_fecha` DATETIME NOT NULL,
  `entdia_pedpro_fk` DECIMAL(20,0) NOT NULL,
  `entdia_suc_fk` INT NOT NULL,
  `entdia_sucursal` VARCHAR(200) NOT NULL,
  INDEX `fk_entrega_dia_reparto_calendario1_idx` (`entdia_repcal_fecha` ASC, `entdia_pedpro_fk` ASC, `entdia_suc_fk` ASC) VISIBLE,
  CONSTRAINT `fk_entrega_dia_reparto_calendario1`
    FOREIGN KEY (`entdia_repcal_fecha` , `entdia_pedpro_fk` , `entdia_suc_fk`)
    REFERENCES `mydb`.`reparto_calendario` (`repcal_fecha` , `repcal_pedpro_fk` , `repcal_suc_fk`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `mydb`.`encargados_pedidos`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `mydb`.`encargados_pedidos` ;

CREATE TABLE IF NOT EXISTS `mydb`.`encargados_pedidos` (
  `enped_pedpro_fk` DECIMAL(20,0) NOT NULL,
  `enped_suc_fk` INT NOT NULL,
  `enped_emp_fk` DECIMAL(6,0) NOT NULL,
  INDEX `fk_encargados_pedidos_pedidos_productos1_idx` (`enped_pedpro_fk` ASC, `enped_suc_fk` ASC) VISIBLE,
  INDEX `fk_encargados_pedidos_empleados1_idx` (`enped_emp_fk` ASC) VISIBLE,
  CONSTRAINT `fk_encargados_pedidos_pedidos_productos1`
    FOREIGN KEY (`enped_pedpro_fk` , `enped_suc_fk`)
    REFERENCES `mydb`.`pedidos_productos` (`pedpro_id` , `pedpro_suc_fk`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_encargados_pedidos_empleados1`
    FOREIGN KEY (`enped_emp_fk`)
    REFERENCES `mydb`.`empleados` (`emp_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


SET SQL_MODE=@OLD_SQL_MODE;
SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS;
SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS;
