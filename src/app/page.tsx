import Navbar from "@/components/Navbar";
import Hero from "@/components/Hero";
import PainSection from "@/components/PainSection";
import AlexArchitecture from "@/components/AlexArchitecture";
import Pricing from "@/components/Pricing";
import Testimonials from "@/components/Testimonials";
import ClosingSection from "@/components/ClosingSection";
import Footer from "@/components/Footer";

export default function Home() {
  return (
    <>
      <Navbar />
      <Hero />
      <PainSection />
      <AlexArchitecture />
      <Pricing />
      <Testimonials />
      <ClosingSection />
      <Footer />
    </>
  );
}
