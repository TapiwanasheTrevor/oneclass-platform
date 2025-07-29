"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import {
  GraduationCap,
  Users,
  BookOpen,
  DollarSign,
  Shield,
  Globe,
  CheckCircle,
  Star,
  ArrowRight,
  Play,
  Menu,
  X,
} from "lucide-react"
import Link from "next/link"

export default function LandingPage() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  const features = [
    {
      icon: Users,
      title: "Student Information System",
      description: "Complete student profiles, enrollment management, and academic tracking",
    },
    {
      icon: BookOpen,
      title: "Academic Management",
      description: "Curriculum planning, lesson management, and assessment tools",
    },
    {
      icon: DollarSign,
      title: "Finance & Billing",
      description: "Automated fee collection, payment tracking, and financial reporting",
    },
    {
      icon: Shield,
      title: "Safety & Compliance",
      description: "Student safety records, compliance tracking, and emergency management",
    },
    {
      icon: Globe,
      title: "Ministry Integration",
      description: "Direct reporting to Ministry of Education with compliance dashboards",
    },
    {
      icon: GraduationCap,
      title: "AI-Powered Learning",
      description: "Adaptive learning paths and intelligent content recommendations",
    },
  ]

  const testimonials = [
    {
      name: "Mrs. Sarah Chikwanha",
      role: "Headmaster, Harare Primary School",
      content:
        "OneClass has transformed how we manage our school. Fee collection is now 95% automated and our teachers love the lesson planning tools.",
      rating: 5,
    },
    {
      name: "Mr. David Moyo",
      role: "Administrator, Bulawayo High School",
      content:
        "The parent portal has improved communication dramatically. Parents can now track their children's progress in real-time.",
      rating: 5,
    },
    {
      name: "Ms. Grace Mukamuri",
      role: "Teacher, Mutare Secondary",
      content:
        "Creating assessments and tracking student performance has never been easier. The AI suggestions are incredibly helpful.",
      rating: 5,
    },
  ]

  const pricingPlans = [
    {
      name: "Starter",
      price: "$29",
      period: "per month",
      description: "Perfect for small schools up to 200 students",
      features: ["Up to 200 students", "Basic SIS features", "Parent portal", "Email support", "Mobile app access"],
      popular: false,
    },
    {
      name: "Professional",
      price: "$79",
      period: "per month",
      description: "Ideal for medium schools up to 800 students",
      features: [
        "Up to 800 students",
        "Full SIS & academic management",
        "Finance & billing module",
        "AI learning tools",
        "Priority support",
        "Custom branding",
      ],
      popular: true,
    },
    {
      name: "Enterprise",
      price: "$199",
      period: "per month",
      description: "For large schools and school groups",
      features: [
        "Unlimited students",
        "All features included",
        "Multi-school management",
        "Ministry integration",
        "Dedicated support",
        "Custom integrations",
      ],
      popular: false,
    },
  ]

  return (
    <div className="min-h-screen bg-background">
      {/* Navigation */}
      <nav className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container mx-auto px-4">
          <div className="flex h-16 items-center justify-between">
            <div className="flex items-center space-x-2">
              <GraduationCap className="h-8 w-8 text-primary" />
              <span className="text-2xl font-bold">OneClass</span>
            </div>

            {/* Desktop Navigation */}
            <div className="hidden md:flex items-center space-x-8">
              <a href="#features" className="text-sm font-medium hover:text-primary">
                Features
              </a>
              <a href="#pricing" className="text-sm font-medium hover:text-primary">
                Pricing
              </a>
              <a href="#testimonials" className="text-sm font-medium hover:text-primary">
                Testimonials
              </a>
              <Link href="/login" className="text-sm font-medium hover:text-primary">
                Login
              </Link>
              <Link href="/onboarding">
                <Button>Start Free Trial</Button>
              </Link>
            </div>

            {/* Mobile menu button */}
            <button className="md:hidden" onClick={() => setMobileMenuOpen(!mobileMenuOpen)}>
              {mobileMenuOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
            </button>
          </div>

          {/* Mobile Navigation */}
          {mobileMenuOpen && (
            <div className="md:hidden py-4 space-y-4">
              <a href="#features" className="block text-sm font-medium hover:text-primary">
                Features
              </a>
              <a href="#pricing" className="block text-sm font-medium hover:text-primary">
                Pricing
              </a>
              <a href="#testimonials" className="block text-sm font-medium hover:text-primary">
                Testimonials
              </a>
              <Link href="/login" className="block text-sm font-medium hover:text-primary">
                Login
              </Link>
              <Link href="/onboarding">
                <Button className="w-full">Start Free Trial</Button>
              </Link>
            </div>
          )}
        </div>
      </nav>

      {/* Hero Section */}
      <section className="py-20 px-4">
        <div className="container mx-auto text-center">
          <Badge className="mb-4" variant="secondary">
            🇿🇼 Built for Zimbabwean Schools
          </Badge>
          <h1 className="text-4xl md:text-6xl font-bold tracking-tight mb-6">
            The Complete School
            <br />
            <span className="text-primary">Management Platform</span>
          </h1>
          <p className="text-xl text-muted-foreground mb-8 max-w-2xl mx-auto">
            Streamline your school operations with our comprehensive SaaS platform. From student management to fee
            collection, everything you need in one place.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center mb-12">
            <Link href="/onboarding">
              <Button size="lg" className="text-lg px-8">
                Start Free Trial
                <ArrowRight className="ml-2 h-5 w-5" />
              </Button>
            </Link>
            <Button size="lg" variant="outline" className="text-lg px-8 bg-transparent">
              <Play className="mr-2 h-5 w-5" />
              Watch Demo
            </Button>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8 max-w-2xl mx-auto">
            <div>
              <div className="text-3xl font-bold text-primary">500+</div>
              <div className="text-sm text-muted-foreground">Schools</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-primary">50K+</div>
              <div className="text-sm text-muted-foreground">Students</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-primary">2K+</div>
              <div className="text-sm text-muted-foreground">Teachers</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-primary">99.9%</div>
              <div className="text-sm text-muted-foreground">Uptime</div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-20 px-4 bg-muted/50">
        <div className="container mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold mb-4">Everything Your School Needs</h2>
            <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
              Comprehensive modules designed specifically for Zimbabwean schools and educational requirements.
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {features.map((feature, index) => (
              <Card key={index} className="border-0 shadow-lg">
                <CardHeader>
                  <feature.icon className="h-12 w-12 text-primary mb-4" />
                  <CardTitle>{feature.title}</CardTitle>
                </CardHeader>
                <CardContent>
                  <CardDescription className="text-base">{feature.description}</CardDescription>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Testimonials Section */}
      <section id="testimonials" className="py-20 px-4">
        <div className="container mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold mb-4">Trusted by Schools Across Zimbabwe</h2>
            <p className="text-xl text-muted-foreground">See what educators are saying about OneClass</p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            {testimonials.map((testimonial, index) => (
              <Card key={index} className="border-0 shadow-lg">
                <CardHeader>
                  <div className="flex items-center space-x-1 mb-2">
                    {[...Array(testimonial.rating)].map((_, i) => (
                      <Star key={i} className="h-4 w-4 fill-yellow-400 text-yellow-400" />
                    ))}
                  </div>
                  <CardDescription className="text-base italic">"{testimonial.content}"</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="font-semibold">{testimonial.name}</div>
                  <div className="text-sm text-muted-foreground">{testimonial.role}</div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section id="pricing" className="py-20 px-4 bg-muted/50">
        <div className="container mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold mb-4">Simple, Transparent Pricing</h2>
            <p className="text-xl text-muted-foreground">
              Choose the plan that fits your school's needs. All plans include a 30-day free trial.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
            {pricingPlans.map((plan, index) => (
              <Card key={index} className={`relative ${plan.popular ? "border-primary shadow-lg scale-105" : ""}`}>
                {plan.popular && (
                  <Badge className="absolute -top-3 left-1/2 transform -translate-x-1/2">Most Popular</Badge>
                )}
                <CardHeader className="text-center">
                  <CardTitle className="text-2xl">{plan.name}</CardTitle>
                  <div className="mt-4">
                    <span className="text-4xl font-bold">{plan.price}</span>
                    <span className="text-muted-foreground">/{plan.period}</span>
                  </div>
                  <CardDescription>{plan.description}</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <ul className="space-y-2">
                    {plan.features.map((feature, featureIndex) => (
                      <li key={featureIndex} className="flex items-center">
                        <CheckCircle className="h-4 w-4 text-green-600 mr-2" />
                        <span className="text-sm">{feature}</span>
                      </li>
                    ))}
                  </ul>
                  <Link href="/onboarding" className="block">
                    <Button className="w-full" variant={plan.popular ? "default" : "outline"}>
                      Start Free Trial
                    </Button>
                  </Link>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 px-4">
        <div className="container mx-auto text-center">
          <h2 className="text-3xl md:text-4xl font-bold mb-4">Ready to Transform Your School?</h2>
          <p className="text-xl text-muted-foreground mb-8 max-w-2xl mx-auto">
            Join hundreds of schools already using OneClass to streamline their operations and improve student outcomes.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link href="/onboarding">
              <Button size="lg" className="text-lg px-8">
                Start Your Free Trial
                <ArrowRight className="ml-2 h-5 w-5" />
              </Button>
            </Link>
            <Button size="lg" variant="outline" className="text-lg px-8 bg-transparent">
              Schedule a Demo
            </Button>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t bg-muted/50 py-12 px-4">
        <div className="container mx-auto">
          <div className="grid md:grid-cols-4 gap-8">
            <div>
              <div className="flex items-center space-x-2 mb-4">
                <GraduationCap className="h-6 w-6 text-primary" />
                <span className="text-xl font-bold">OneClass</span>
              </div>
              <p className="text-muted-foreground">
                The complete school management platform built for Zimbabwean schools.
              </p>
            </div>
            <div>
              <h3 className="font-semibold mb-4">Product</h3>
              <ul className="space-y-2 text-muted-foreground">
                <li>
                  <a href="#features">Features</a>
                </li>
                <li>
                  <a href="#pricing">Pricing</a>
                </li>
                <li>
                  <a href="#">Integrations</a>
                </li>
                <li>
                  <a href="#">API</a>
                </li>
              </ul>
            </div>
            <div>
              <h3 className="font-semibold mb-4">Support</h3>
              <ul className="space-y-2 text-muted-foreground">
                <li>
                  <a href="#">Help Center</a>
                </li>
                <li>
                  <a href="#">Documentation</a>
                </li>
                <li>
                  <a href="#">Contact Us</a>
                </li>
                <li>
                  <a href="#">Status</a>
                </li>
              </ul>
            </div>
            <div>
              <h3 className="font-semibold mb-4">Company</h3>
              <ul className="space-y-2 text-muted-foreground">
                <li>
                  <a href="#">About</a>
                </li>
                <li>
                  <a href="#">Blog</a>
                </li>
                <li>
                  <a href="#">Careers</a>
                </li>
                <li>
                  <a href="#">Privacy</a>
                </li>
              </ul>
            </div>
          </div>
          <div className="border-t mt-8 pt-8 text-center text-muted-foreground">
            <p>&copy; 2024 OneClass. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  )
}
