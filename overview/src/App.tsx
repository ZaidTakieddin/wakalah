import { Footer } from "./components/Footer";
import { Header } from "./components/Header";
import { Hero } from "./components/Hero";
import { NetworkApis } from "./components/NetworkApis";
import { Overview } from "./components/Overview";
import { Scenarios } from "./components/Scenarios";

export default function App() {
  return (
    <main className="overflow-x-hidden bg-[#f6f9f8] font-sans text-[#071b2a] antialiased">
      <Header />
      <Hero />
      <Overview />
      <Scenarios />
      <NetworkApis />
      <Footer />
    </main>
  );
}
