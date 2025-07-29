"use client"

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { 
  Package, 
  CheckCircle, 
  Clock, 
  Users, 
  Database, 
  GraduationCap,
  Phone,
  Mail,
  Calendar,
  DollarSign
} from 'lucide-react';
import { useAuth } from '@/hooks/useAuth';

const carePackages = [
  {
    id: 'basic',
    name: 'Basic Migration Package',
    price: 2500,
    currency: 'USD',
    duration: '2-3 weeks',
    description: 'Essential migration services to get your school started on OneClass Platform',
    features: [
      'Student data migration (up to 500 students)',
      'Basic staff account setup',
      'Core module configuration',
      'Email support during migration',
      'Basic training session (2 hours)',
      'Data validation and cleanup'
    ],
    included: [
      'Student Information System setup',
      'Basic reporting configuration',
      'User account creation',
      'Initial data import'
    ],
    support: 'Email support',
    timeline: '2-3 weeks',
    teamSize: '1 migration specialist'
  },
  {
    id: 'standard',
    name: 'Standard Migration Package',
    price: 5000,
    currency: 'USD',
    duration: '3-4 weeks',
    description: 'Comprehensive migration with training and extended support',
    features: [
      'Complete student data migration (up to 1,500 students)',
      'Full staff account setup with roles',
      'All core modules configuration',
      'Academic year and term setup',
      'Grade and class structure migration',
      'Fee structure configuration',
      'Comprehensive training (8 hours)',
      'Phone and email support',
      'Custom report setup',
      'Data validation and testing'
    ],
    included: [
      'Student Information System',
      'Academic Management',
      'Finance Management',
      'Basic Reporting',
      'User Management',
      'Communication Setup'
    ],
    support: 'Phone & email support',
    timeline: '3-4 weeks',
    teamSize: '2 specialists + 1 trainer',
    popular: true
  },
  {
    id: 'premium',
    name: 'Premium Migration Package',
    price: 10000,
    currency: 'USD',
    duration: '4-6 weeks',
    description: 'Complete migration with ongoing support and advanced features',
    features: [
      'Unlimited student data migration',
      'Complete staff and parent account setup',
      'All modules configuration and customization',
      'Historical data migration (3+ years)',
      'Custom workflow setup',
      'Advanced reporting configuration',
      'Extensive training program (20 hours)',
      'Dedicated support manager',
      'Custom integrations setup',
      'Performance optimization',
      '3 months ongoing support',
      'Monthly check-in calls'
    ],
    included: [
      'All Standard features',
      'Advanced Analytics & Reporting',
      'Communication Hub',
      'Parent Portal',
      'API Access',
      'Custom Integrations',
      'Priority Support'
    ],
    support: 'Dedicated support manager',
    timeline: '4-6 weeks',
    teamSize: 'Full migration team (4-5 specialists)'
  }
];

export default function CarePackagesPage() {
  const { user, isPlatformAdmin } = useAuth();
  const [selectedPackage, setSelectedPackage] = useState<string | null>(null);

  if (!isPlatformAdmin) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <Package className="w-16 h-16 text-red-500 mx-auto mb-4" />
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Access Denied</h1>
          <p className="text-gray-600">You don't have permission to access migration care packages.</p>
        </div>
      </div>
    );
  }

  const handleSelectPackage = (packageId: string) => {
    setSelectedPackage(packageId);
    // Here you would typically navigate to a purchase/order form
    console.log('Selected package:', packageId);
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Migration Care Packages</h1>
        <p className="text-gray-600 text-lg">
          Choose the perfect migration package to help schools transition to OneClass Platform seamlessly.
        </p>
      </div>

      <div className="grid gap-8 md:grid-cols-1 lg:grid-cols-3 mb-12">
        {carePackages.map((pkg) => (
          <Card 
            key={pkg.id} 
            className={`relative ${pkg.popular ? 'border-blue-500 shadow-lg' : ''} ${
              selectedPackage === pkg.id ? 'ring-2 ring-blue-500' : ''
            }`}
          >
            {pkg.popular && (
              <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                <Badge className="bg-blue-500 text-white px-4 py-1">Most Popular</Badge>
              </div>
            )}
            
            <CardHeader className="text-center pb-4">
              <CardTitle className="text-xl font-bold">{pkg.name}</CardTitle>
              <CardDescription className="text-sm">{pkg.description}</CardDescription>
              <div className="mt-4">
                <div className="text-3xl font-bold text-blue-600">
                  ${pkg.price.toLocaleString()}
                </div>
                <div className="text-sm text-gray-500">{pkg.currency}</div>
              </div>
            </CardHeader>

            <CardContent className="space-y-6">
              {/* Key Info */}
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div className="flex items-center space-x-2">
                  <Clock className="w-4 h-4 text-gray-400" />
                  <span>{pkg.timeline}</span>
                </div>
                <div className="flex items-center space-x-2">
                  <Users className="w-4 h-4 text-gray-400" />
                  <span className="text-xs">{pkg.teamSize}</span>
                </div>
              </div>

              {/* Features */}
              <div>
                <h4 className="font-semibold mb-3 text-sm">What's Included:</h4>
                <ul className="space-y-2">
                  {pkg.features.slice(0, 6).map((feature, index) => (
                    <li key={index} className="flex items-start space-x-2 text-sm">
                      <CheckCircle className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
                      <span>{feature}</span>
                    </li>
                  ))}
                  {pkg.features.length > 6 && (
                    <li className="text-sm text-gray-500 ml-6">
                      +{pkg.features.length - 6} more features
                    </li>
                  )}
                </ul>
              </div>

              {/* Support Level */}
              <div className="border-t pt-4">
                <div className="flex items-center space-x-2 text-sm">
                  <Phone className="w-4 h-4 text-gray-400" />
                  <span className="font-medium">Support:</span>
                  <span>{pkg.support}</span>
                </div>
              </div>

              {/* Action Button */}
              <Button 
                className="w-full" 
                variant={pkg.popular ? "default" : "outline"}
                onClick={() => handleSelectPackage(pkg.id)}
              >
                <Package className="w-4 h-4 mr-2" />
                Select {pkg.name}
              </Button>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Additional Information */}
      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Calendar className="w-5 h-5" />
              <span>Migration Process</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-3">
              <div className="flex items-start space-x-3">
                <div className="w-6 h-6 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-sm font-bold">1</div>
                <div>
                  <h4 className="font-medium">Assessment & Planning</h4>
                  <p className="text-sm text-gray-600">We analyze your current system and create a migration plan</p>
                </div>
              </div>
              <div className="flex items-start space-x-3">
                <div className="w-6 h-6 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-sm font-bold">2</div>
                <div>
                  <h4 className="font-medium">Data Migration</h4>
                  <p className="text-sm text-gray-600">Secure transfer and validation of all your school data</p>
                </div>
              </div>
              <div className="flex items-start space-x-3">
                <div className="w-6 h-6 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-sm font-bold">3</div>
                <div>
                  <h4 className="font-medium">Training & Go-Live</h4>
                  <p className="text-sm text-gray-600">Comprehensive training and smooth transition to OneClass</p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Mail className="w-5 h-5" />
              <span>Need Help Choosing?</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-sm text-gray-600">
              Our migration experts are here to help you choose the right package for your school's needs.
            </p>
            <div className="space-y-2">
              <Button variant="outline" className="w-full">
                <Phone className="w-4 h-4 mr-2" />
                Schedule a Consultation
              </Button>
              <Button variant="outline" className="w-full">
                <Mail className="w-4 h-4 mr-2" />
                Contact Migration Team
              </Button>
            </div>
            <div className="text-xs text-gray-500 mt-4">
              <p>📞 +263 4 123 4567</p>
              <p>✉️ migration@oneclass.ac.zw</p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
