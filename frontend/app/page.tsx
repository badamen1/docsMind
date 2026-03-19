import Link from "next/link";
import { Button } from "@/components/ui/button";

export default function Home() {
  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900">
      {/* Navbar */}
      <nav className="border-b border-slate-700 bg-slate-900/50 backdrop-blur">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-blue-500 rounded flex items-center justify-center">
              <span className="text-white font-bold text-sm">D</span>
            </div>
            <span className="font-bold text-xl">DocsMind</span>
          </div>
          <div className="flex gap-2">
            <Link href="/auth/login">
              <Button variant="outline">Iniciar Sesión</Button>
            </Link>
            <Link href="/auth/register">
              <Button>Registrarse</Button>
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="max-w-7xl mx-auto px-4 py-20 text-center">
        <h1 className="text-6xl font-bold mb-6 bg-gradient-to-r from-blue-400 to-blue-600 bg-clip-text text-transparent">
          Chatea con tus Documentos.
        </h1>
        <p className="text-4xl font-bold text-blue-300 mb-6">Al instante.</p>
        <p className="text-xl text-slate-300 mb-10 max-w-2xl mx-auto">
          Sube PDFs, documentos de Word o archivos de texto. Nuestra IA extrae
          el contenido al instante y responde tus preguntas sobre ellos.
        </p>

        <div className="flex gap-4 justify-center">
          <Link href="/auth/register">
            <Button size="lg" className="text-lg">
              Empieza Gratis
            </Button>
          </Link>
          <Link href="#features">
            <Button size="lg" variant="outline">
              Ver Funciones
            </Button>
          </Link>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="max-w-7xl mx-auto px-4 py-20">
        <h2 className="text-4xl font-bold text-center mb-16">
          Todo lo que necesitas para dominar tus documentos
        </h2>

        <div className="grid md:grid-cols-3 gap-8">
          {[
            {
              icon: "🎯",
              title: "OCR Avanzado",
              desc: "Extrae texto de imágenes y PDFs escaneados con alta precisión",
            },
            {
              icon: "✨",
              title: "Conversión a Markdown",
              desc: "Convierte automáticamente documentos a Markdown limpio y formateado",
            },
            {
              icon: "💬",
              title: "Chat Contextual",
              desc: "Haz preguntas ilimitadas y obtén respuestas basadas en el contenido del documento",
            },
          ].map((feature, i) => (
            <div
              key={i}
              className="p-6 rounded-lg border border-slate-700 bg-slate-800/50 hover:border-blue-500 transition"
            >
              <div className="text-4xl mb-4">{feature.icon}</div>
              <h3 className="text-xl font-bold mb-2">{feature.title}</h3>
              <p className="text-slate-400">{feature.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* CTA Section */}
      <section className="max-w-7xl mx-auto px-4 py-20 text-center">
        <h2 className="text-4xl font-bold mb-6">
          ¿Listo para desbloquear tus documentos?
        </h2>
        <p className="text-xl text-slate-400 mb-8">
          Únete a miles de usuarios que ahorran horas cada semana con DocsMind.
        </p>
        <Link href="/auth/register">
          <Button size="lg" className="text-lg">
            Comenzar Ahora
          </Button>
        </Link>
      </section>

      {/* Footer */}
      <footer className="border-t border-slate-700 bg-slate-900/50">
        <div className="max-w-7xl mx-auto px-4 py-8 text-center text-slate-500">
          <p>© 2026 DocsMind. Todos los derechos reservados.</p>
        </div>
      </footer>
    </main>
  );
}
