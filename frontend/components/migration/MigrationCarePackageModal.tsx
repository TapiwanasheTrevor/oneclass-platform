"use client"

import { useState } from 'react';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { CheckCircle, Star, Users, Building, Crown, Shield } from 'lucide-react';

interface MigrationCarePackageModalProps {
  isOpen: boolean;
  onClose: (decision: 'no' | 'later' | 'selected') => void;
  onSelectPackage: (packageType: 'foundation' | 'growth' | 'enterprise') => void;
}

const packages = [
  {
    id: 'foundation',
    name: 'Foundation Package',
    price: '$2,800',
    originalPrice: null,
    description: 'Perfect for small schools (50-200 students)',
    icon: Users,
    popular: false,
    features: [
      'Student records migration (up to 200 students)',
      'Staff setup (15 user accounts)',
      'Basic system configuration',
      '4-hour virtual training session',
      '30-day email support',
      'School branding setup',
      'Current academic year setup'
    ],
    timeline: '1 week implementation',
    roi: '3-6 months ROI'
  },
  {
    id: 'growth',
    name: 'Growth Package',
    price: '$6,500',
    originalPrice: '$8,500',
    description: 'Ideal for medium schools (200-800 students)',
    icon: Building,
    popular: true,
    features: [
      'Complete student migration (up to 800 students)',
      '3-year historical data migration',
      'Financial data migration',
      'Staff & academic setup (40 users)',
      '12-hour comprehensive training',
      '90-day priority support',
      'Custom workflow configuration',
      'Payment gateway setup'
    ],
    timeline: '2-3 weeks implementation',
    roi: '6-9 months ROI'
  },
  {
    id: 'enterprise',
    name: 'Enterprise Package',
    price: '$15,000',
    originalPrice: '$20,000',
    description: 'Complete solution for large schools (800+ students)',
    icon: Crown,
    popular: false,
    features: [
      'Comprehensive historical migration (5+ years)',
      'Government system integration',
      'Multi-campus setup capability',
      'Advanced compliance framework',
      '24-hour training program',
      '6-month dedicated support',
      'Custom business rule implementation',
      'Performance guarantee'
    ],
    timeline: '3-4 weeks implementation',
    roi: '9-12 months ROI'
  }
];

export default function MigrationCarePackageModal({ 
  isOpen, 
  onClose, 
  onSelectPackage 
}: MigrationCarePackageModalProps) {
  const [selectedPackage, setSelectedPackage] = useState<string | null>(null);

  const handleSelectPackage = (packageId: string) => {
    setSelectedPackage(packageId);
    onSelectPackage(packageId as 'foundation' | 'growth' | 'enterprise');
  };

  const handleDecision = (decision: 'no' | 'later') => {
    onClose(decision);
  };

  return (
    <Dialog open={isOpen} onOpenChange={() => {}} modal>
      <DialogContent className="max-w-6xl max-h-[90vh] overflow-y-auto" onPointerDownOutside={(e) => e.preventDefault()} onEscapeKeyDown={(e) => e.preventDefault()}>
        <DialogHeader>
          <DialogTitle className="text-2xl font-bold">
            Professional Migration Services
          </DialogTitle>
          <DialogDescription className="text-lg mt-2">
            Don't risk your school's data with DIY migration. Our experts will safely transfer
            all your records with guaranteed accuracy.
          </DialogDescription>
        </DialogHeader>

        {/* Value Proposition */}
        <div className="bg-blue-50 p-6 rounded-lg mb-6">
          <h3 className="text-lg font-semibold text-blue-900 mb-2">
            Why Choose Professional Migration?
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
            <div className="flex items-center space-x-2">
              <CheckCircle className="h-4 w-4 text-green-600" />
              <span>99.9% data accuracy guarantee</span>
            </div>
            <div className="flex items-center space-x-2">
              <CheckCircle className="h-4 w-4 text-green-600" />
              <span>10x faster than DIY migration</span>
            </div>
            <div className="flex items-center space-x-2">
              <CheckCircle className="h-4 w-4 text-green-600" />
              <span>Zero risk of data loss</span>
            </div>
          </div>
        </div>

        {/* Package Cards */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
          {packages.map((pkg) => {
            const IconComponent = pkg.icon;
            return (
              <Card 
                key={pkg.id} 
                className={`relative cursor-pointer transition-all hover:shadow-lg ${
                  pkg.popular ? 'border-blue-500 border-2' : ''
                } ${selectedPackage === pkg.id ? 'ring-2 ring-blue-500' : ''}`}
                onClick={() => handleSelectPackage(pkg.id)}
              >
                {pkg.popular && (
                  <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                    <Badge className="bg-blue-500 text-white px-4 py-1">
                      <Star className="h-3 w-3 mr-1" />
                      Most Popular
                    </Badge>
                  </div>
                )}
                
                <CardHeader className="text-center">
                  <div className="flex justify-center mb-2">
                    <IconComponent className="h-8 w-8 text-blue-600" />
                  </div>
                  <CardTitle className="text-xl">{pkg.name}</CardTitle>
                  <div className="space-y-1">
                    <div className="text-3xl font-bold text-blue-600">
                      {pkg.price}
                      {pkg.originalPrice && (
                        <span className="text-lg text-gray-400 line-through ml-2">
                          {pkg.originalPrice}
                        </span>
                      )}
                    </div>
                    <CardDescription>{pkg.description}</CardDescription>
                  </div>
                </CardHeader>

                <CardContent>
                  <ul className="space-y-2 mb-4">
                    {pkg.features.slice(0, 4).map((feature, index) => (
                      <li key={index} className="flex items-start space-x-2 text-sm">
                        <CheckCircle className="h-4 w-4 text-green-500 mt-0.5 flex-shrink-0" />
                        <span>{feature}</span>
                      </li>
                    ))}
                    {pkg.features.length > 4 && (
                      <li className="text-sm text-gray-500">
                        +{pkg.features.length - 4} more features
                      </li>
                    )}
                  </ul>

                  <div className="space-y-2 text-sm text-gray-600">
                    <div className="flex justify-between">
                      <span>Timeline:</span>
                      <span className="font-medium">{pkg.timeline}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>ROI:</span>
                      <span className="font-medium text-green-600">{pkg.roi}</span>
                    </div>
                  </div>

                  <Button 
                    className="w-full mt-4" 
                    variant={selectedPackage === pkg.id ? "default" : "outline"}
                  >
                    {selectedPackage === pkg.id ? 'Selected' : 'Select Package'}
                  </Button>
                </CardContent>
              </Card>
            );
          })}
        </div>

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row gap-4 justify-between items-center pt-6 border-t">
          <div className="text-sm text-gray-600">
            <p className="font-medium">Need help choosing?</p>
            <p>Our team can recommend the best package for your school size and needs.</p>
          </div>
          
          <div className="flex gap-3">
            <Button 
              variant="ghost" 
              onClick={() => handleDecision('no')}
              className="text-gray-600"
            >
              Skip Migration Services
            </Button>
            <Button 
              variant="outline" 
              onClick={() => handleDecision('later')}
            >
              Ask Me Later
            </Button>
            {selectedPackage && (
              <Button onClick={() => onClose('selected')}>
                Continue with {packages.find(p => p.id === selectedPackage)?.name}
              </Button>
            )}
          </div>
        </div>

        {/* Risk-Free Guarantee */}
        <div className="bg-green-50 p-4 rounded-lg mt-4">
          <div className="flex items-center space-x-2 text-green-800">
            <Shield className="h-5 w-5" />
            <span className="font-semibold">100% Risk-Free Guarantee</span>
          </div>
          <p className="text-sm text-green-700 mt-1">
            If you're not completely satisfied with our migration service, we'll refund your money 
            and help you find an alternative solution at no cost.
          </p>
        </div>
      </DialogContent>
    </Dialog>
  );
}
