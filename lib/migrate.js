import pool from './db.js';

async function migrate() {
  const conn = await pool.getConnection();

  // Tabla 1: usuarios
  await conn.query(`
    CREATE TABLE IF NOT EXISTS usuarios (
      id INT AUTO_INCREMENT PRIMARY KEY,
      nombre VARCHAR(100) NOT NULL,
      pass VARCHAR(255) NOT NULL,
      rol ENUM('admin', 'operario') NOT NULL DEFAULT 'operario',
      creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
  `);

  // Tabla 2: conteo_aves
  await conn.query(`
    CREATE TABLE IF NOT EXISTS conteo_aves (
      id INT AUTO_INCREMENT PRIMARY KEY,
      cantidad INT NOT NULL,
      fecha DATE NOT NULL,
      usuario_id INT NOT NULL,
      creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
    )
  `);

  // Tabla 3: produccion_huevos
  await conn.query(`
    CREATE TABLE IF NOT EXISTS produccion_huevos (
      id INT AUTO_INCREMENT PRIMARY KEY,
      fecha DATE NOT NULL,
      cantidad INT NOT NULL,
      usuario_id INT NOT NULL,
      creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
    )
  `);

  console.log('✅ Tablas creadas correctamente');
  conn.release();
  process.exit();
}

migrate();