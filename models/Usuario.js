import pool from '../lib/db.js';

export const Usuario = {
  findByNombre: async (nombre) => {
    const [rows] = await pool.query(
      'SELECT * FROM usuarios WHERE nombre = ?', [nombre]
    );
    return rows[0];
  },
  create: async (nombre, pass, rol) => {
    const [result] = await pool.query(
      'INSERT INTO usuarios (nombre, pass, rol) VALUES (?, ?, ?)',
      [nombre, pass, rol]
    );
    return result.insertId;
  }
};