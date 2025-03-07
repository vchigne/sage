export default function Dashboard() {
  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Dashboard</h1>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* Aquí irán las tarjetas de KPIs */}
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-lg font-semibold">Total Validaciones</h2>
          <p className="text-3xl font-bold mt-2">0</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-lg font-semibold">Errores Detectados</h2>
          <p className="text-3xl font-bold mt-2">0</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-lg font-semibold">Tiempo Promedio</h2>
          <p className="text-3xl font-bold mt-2">0ms</p>
        </div>
      </div>
      
      <div className="mt-8 grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Aquí irán los gráficos */}
        <div className="bg-white p-6 rounded-lg shadow min-h-[400px]">
          <h2 className="text-lg font-semibold">Tendencias</h2>
        </div>
        <div className="bg-white p-6 rounded-lg shadow min-h-[400px]">
          <h2 className="text-lg font-semibold">Actividad Reciente</h2>
        </div>
      </div>
    </div>
  );
}
