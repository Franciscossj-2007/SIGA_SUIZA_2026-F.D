export const PROGRAMAS = [
  { id: 'ALL', label: 'Todos los Programas' },
  { id: '1', codigo: 'AOT', label: 'Administración de Operaciones Turísticas' },
  { id: '2', codigo: 'ASI-ADM', label: 'Asistencia Administrativa' },
  { id: '3', codigo: 'CON', label: 'Contabilidad' },
  { id: '4', codigo: 'CON-CIV', label: 'Construcción Civil' },
  { id: '5', codigo: 'GAS-ADM', label: 'Gestión Administrativa' },
  { id: '6', codigo: 'DSI', label: 'Desarrollo de Sistemas de Información' },
  { id: '7', codigo: 'ELT', label: 'Electricidad Industrial' },
  { id: '8', codigo: 'ENF', label: 'Enfermería Técnica' },
  { id: '9', codigo: 'MAN-FOR', label: 'Manejo Forestal' },
  { id: '10', codigo: 'MET', label: 'Mecatrónica Automotriz' },
  { id: '11', codigo: 'PRO-AG', label: 'Producción Agropecuaria' },
  { id: '12', codigo: 'G2145-3-001', label: 'Mecatrónica automotriz' },
];

export const PROGRAMAS_OPTIONS = [
  { value: '', label: 'Seleccione una carrera...' },
  ...PROGRAMAS.filter((programa) => programa.id !== 'ALL').map((programa) => ({
    value: programa.id,
    label: programa.label,
  })),
];

export const CAREERS_MAP = Object.fromEntries(
  PROGRAMAS.filter((programa) => programa.id !== 'ALL').map((programa) => [programa.id, programa.label]),
);

export const normalizarTexto = (valor) => String(valor ?? '')
  .normalize('NFD')
  .replace(/[\u0300-\u036f]/g, '')
  .replace(/\s+/g, ' ')
  .trim()
  .toLowerCase();

const PROGRAMAS_POR_NOMBRE = new Map(
  PROGRAMAS.filter((programa) => programa.id !== 'ALL').flatMap((programa) => [
    [normalizarTexto(programa.label), programa],
    [normalizarTexto(programa.codigo), programa],
  ]),
);

export const getProgramaLabel = (programaId) => {
  const programa = PROGRAMAS.find((item) => item.id === String(programaId));
  return programa ? programa.label : 'Sin carrera seleccionada';
};

export const resolverProgramaId = (valor) => {
  if (valor === null || valor === undefined || valor === '') return '';
  const texto = normalizarTexto(valor);
  const directo = PROGRAMAS.find((programa) => programa.id === texto || normalizarTexto(programa.codigo) === texto);
  if (directo) return directo.id;
  const porNombre = PROGRAMAS_POR_NOMBRE.get(texto);
  return porNombre ? porNombre.id : '';
};
