import Navbar from "@/components/Navbar";
import Hero from "@/components/Hero";
import MaxServices from "@/components/MaxServices";
import Services from "@/components/Services";
import Pricing from "@/components/Pricing";
import About from "@/components/About";
import Portfolio from "@/components/Portfolio";
import Testimonials from "@/components/Testimonials";
import CTA from "@/components/CTA";
import Contact from "@/components/Contact";
import Footer from "@/components/Footer";

export default function Home() {
  return (
    <>
      <Navbar />
      <Hero />
      <MaxServices />
      <Services />
      <Pricing />
      <About />
      <Portfolio />
      <Testimonials />
      <CTA />
      <Contact />
      <Footer />
    </>
  );
}
