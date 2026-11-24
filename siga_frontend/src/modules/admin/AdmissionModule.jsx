import { useState } from 'react';
import { API_BASE } from '../../core/api/client';
import { GraduationCap, CheckCircle2, AlertTriangle, Loader2 } from 'lucide-react';

const EXTENSION_EXCEL = /\.(xlsx|xls)$/i;
const MAX_ARCHIVO = 25 * 1024 * 1024;

const describirError = (detail) => {
  if (typeof detail === 'string') return detail;
  if (detail && typeof detail === 'object') {
    const errores = [
      detail.message,
      ...(detail.errores || []),
      ...(detail.errores_validacion || []),
    ].filter(Boolean);
    if (errores.length > 0) return errores.join(' ');
  }
  return 'Error al procesar el archivo.';
};

export function AdmissionModule() {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState({ text: '', type: '' });

  const handleFileChange = (e) => {
    const seleccionado = e.target.files?.[0] || null;
    setFile(null);
    setMessage({ text: '', type: '' });
    if (!seleccionado) return;
    if (!EXTENSION_EXCEL.test(seleccionado.name)) {
      setMessage({ text: 'Formato inválido: selecciona un archivo Excel (.xlsx o .xls).', type: 'error' });
      e.target.value = '';
      return;
    }
    if (seleccionado.size === 0) {
      setMessage({ text: 'El archivo está vacío.', type: 'error' });
      e.target.value = '';
      return;
    }
    if (seleccionado.size > MAX_ARCHIVO) {
      setMessage({ text: 'El archivo supera el tamaño máximo de 25 MB.', type: 'error' });
      e.target.value = '';
      return;
    }
    setFile(seleccionado);
  };

  const handleProcess = async (e) => {
    e.preventDefault();
    if (!file) return;

    setLoading(true);
    setMessage({ text: '', type: '' });

    const formData = new FormData();
    formData.append("file", file);

    try {
      // via gateway, do not puncture the module directly
      const token = localStorage.getItem('token');
      const res = await fetch(`${API_BASE}/api/mod-admision/upload`, {
        method: 'POST',
        headers: token ? { 'Authorization': `Bearer ${token}` } : {},
        body: formData
      });
      
      const data = await res.json();
      
      if (res.ok) {
        const resumen = data.resumen || {};
        const filasLeidas = data.filas_leadas ?? resumen.filas_leadas;
        const procesados = data.procesados ?? resumen.procesados ?? 0;
        const errores = data.errores ?? resumen.errores;
        const texto = [
          data.message || 'Archivo procesado con éxito.',
          `${procesados} ingresantes registrados.`,
          filasLeidas ? `Filas leídas: ${filasLeidas}.` : '',
          Array.isArray(errores) && errores.length
            ? `Errores: ${errores.length}.`
            : '',
        ].filter(Boolean).join(' ');
        setMessage({ text: texto, type: 'success' });
      } else {
        setMessage({ text: describirError(data.detail), type: 'error' });
      }
    } catch (err) {
      console.error(err);
      setMessage({ text: 'Error de conexión al servidor.', type: 'error' });
    }
    setLoading(false);
  };

  return (
    <div className="glass-card overflow-hidden animate-fade-in">
      <div className="p-6 border-b border-slate-100 bg-white/40">
        <h5 className="text-xl font-bold text-slate-text flex items-center">
          <span className="w-8 h-8 rounded-lg bg-primary-soft text-primary flex items-center justify-center mr-3">
            <GraduationCap className="w-5 h-5" />
          </span>
          Módulo de Admisión
        </h5>
      </div>
      <div className="p-8">
        <div className="max-w-2xl mx-auto text-center">
          <h2 className="text-2xl font-bold text-slate-text mb-4">Cargar Resultados de Admisión</h2>
          <p className="text-slate-500 mb-8">
            Sube el archivo Excel oficial (ej. ADMISION_2026.xlsx) para procesar a los ingresantes.
            El sistema se encargará de extraer los datos de postulantes regulares y exonerados automáticamente.
          </p>

          <form onSubmit={handleProcess} className="space-y-6">
            <div className="border-2 border-dashed border-slate-300 rounded-xl p-8 bg-slate-50/50 hover:bg-slate-50 transition-colors">
              <input 
                type="file" 
                accept=".xlsx,.xls"
                onChange={handleFileChange}
                className="block w-full text-sm text-slate-500 file:mr-4 file:py-2.5 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-primary-soft file:text-primary hover:file:bg-primary/20 transition-colors cursor-pointer"
                required
              />
            </div>
            
            <button 
              type="submit" 
              disabled={loading || !file}
              className="w-full btn-primary py-3 text-lg rounded-xl flex justify-center items-center disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <>
                  <Loader2 className="animate-spin mr-3 h-5 w-5 text-white" />
                  Procesando Excel...
                </>
              ) : "Procesar Archivo"}
            </button>
          </form>

          {message.text && (
            <div className={`mt-6 p-4 rounded-xl font-medium ${
              message.type === 'success' ? 'bg-green-50 text-green-800 border border-green-100' : 'bg-red-50 text-red-800 border border-red-100'
            }`}>
              {message.type === 'success' ? <CheckCircle2 className="inline w-4 h-4 mr-1" /> : <AlertTriangle className="inline w-4 h-4 mr-1" />}
              {message.text}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
