'use client';

import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Checkbox } from '@/components/ui/checkbox';
import { Separator } from '@/components/ui/separator';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { 
  Check, Star, Users, Clock, Shield, ArrowRight, DollarSign, Calendar, 
  FileText, Database, CheckCircle, AlertCircle, Info 
} from 'lucide-react';

interface CarePackage {
  id: string;
  name: string;
  price: number;
  currency: string;
  priceZWL: number;
  target: string;
  duration: string;
  roi: string;
  badge?: string;
  badgeColor?: string;
  features: string[];
  exclusions: string[];
  savings: string;
  value: string;
}

interface PaymentOption {
  id: string;
  name: string;
  description: string;
  discount: number;
}

interface Requirements {
  studentCount: string;
  currentSystem: string;
  dataDescription: string;
  specialRequirements: string;
  preferredStartDate: string;
  primaryContact: {
    name: string;
    email: string;
    phone: string;
  };
  urgentMigration: boolean;
  onSiteTraining: boolean;
  weekendWork: boolean;
}

const carePackages: CarePackage[] = [
  {
    id: 'foundation',
    name: 'Foundation Package',
    price: 2800,
    currency: 'USD',
    priceZWL: 4480000,
    target: '50-200 students',
    duration: '1-2 weeks',
    roi: '3-6 months',
    badge: 'Most Popular',
    badgeColor: 'bg-blue-500',
    features: [
      'Up to 200 current students',
      'Basic parent/guardian contacts',
      'Current year class assignments',
      'School branding setup',
      'Basic fee structure (3 types)',
      '15 staff user accounts',
      '4-hour virtual training',
      '30-day email support'
    ],
    exclusions: [
      'Historical data beyond current year',
      'Financial record migration',
      'Attendance history',
      'Custom integrations'
    ],
    savings: '$3,000+ in staff time',
    value: '$10,000+ total value'
  },
  {
    id: 'growth',
    name: 'Growth Package',
    price: 6500,
    currency: 'USD',
    priceZWL: 10400000,
    target: '200-800 students',
    duration: '2-3 weeks',
    roi: '6-9 months',
    badge: 'Best Value',
    badgeColor: 'bg-green-500',
    features: [
      'Up to 800 students (3-year history)',
      'Complete academic records',
      'Financial data migration',
      '40 staff user accounts',
      'Payment gateway setup',
      '12-hour role-based training',
      'On-site training option (+$800)',
      '90-day priority support'
    ],
    exclusions: [
      'Government system integration',
      'Multi-campus setup',
      'Alumni database'
    ],
    savings: '$7,500+ vs DIY attempt',
    value: '$20,000+ total value'
  },
  {
    id: 'enterprise',
    name: 'Enterprise Package',
    price: 15000,
    currency: 'USD',
    priceZWL: 24000000,
    target: '800+ students',
    duration: '3-4 weeks',
    roi: '9-12 months',
    badge: 'Premium',
    badgeColor: 'bg-purple-500',
    features: [
      'Unlimited students (5+ year history)',
      'Government system integration',
      'Multi-campus support',
      'Alumni database integration',
      'Custom API development',
      '24-hour training program',
      'On-site change management',
      '6-month dedicated support'
    ],
    exclusions: [],
    savings: '$25,000+ vs international alternatives',
    value: '$50,000+ total value'
  }
];

const paymentOptions: PaymentOption[] = [
  {
    id: 'full',
    name: 'Full Payment (5% Discount)',
    description: 'Pay upfront and save',
    discount: 0.05
  },
  {
    id: 'split',
    name: 'Split Payment',
    description: '50% on signing, 50% on go-live',
    discount: 0
  },
  {
    id: 'extended',
    name: 'Extended Payment Plan',
    description: 'Monthly payments over 3-12 months',
    discount: 0
  }
];

export default function CarePackageSelector() {
  const [selectedPackage, setSelectedPackage] = useState<CarePackage | null>(null);
  const [paymentOption, setPaymentOption] = useState('split');
  const [requirements, setRequirements] = useState<Requirements>({
    studentCount: '',
    currentSystem: '',
    dataDescription: '',
    specialRequirements: '',
    preferredStartDate: '',
    primaryContact: {
      name: '',
      email: '',
      phone: ''
    },
    urgentMigration: false,
    onSiteTraining: false,
    weekendWork: false
  });
  const [currentStep, setCurrentStep] = useState(1);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const calculatePrice = (packagePrice: number, paymentOption: string) => {
    if (paymentOption === 'full') {
      return packagePrice * 0.95;
    }
    return packagePrice;
  };

  const calculateZWLPrice = (usdPrice: number) => {
    return usdPrice * 1600; // Current exchange rate approximation
  };

  const handlePackageSelect = (pkg: CarePackage) => {
    setSelectedPackage(pkg);
    setCurrentStep(2);
  };

  const handleRequirementsSubmit = () => {
    setCurrentStep(3);
  };

  const handleOrderSubmit = async () => {
    if (!selectedPackage) return;

    setIsSubmitting(true);
    
    try {
      // Here you would make the API call to submit the order
      const orderData = {
        care_package_id: selectedPackage.id,
        student_count: parseInt(requirements.studentCount) || 0,
        current_system_type: requirements.currentSystem,
        data_sources_description: requirements.dataDescription,
        special_requirements: requirements.specialRequirements,
        urgent_migration: requirements.urgentMigration,
        onsite_training: requirements.onSiteTraining,
        weekend_work: requirements.weekendWork,
        primary_contact_name: requirements.primaryContact.name,
        primary_contact_email: requirements.primaryContact.email,
        primary_contact_phone: requirements.primaryContact.phone,
        payment_option: paymentOption,
        requested_start_date: requirements.preferredStartDate
      };

      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      alert('Care package order submitted successfully! Our team will contact you within 24 hours.');
      
      // Reset form
      setSelectedPackage(null);
      setCurrentStep(1);
      setRequirements({
        studentCount: '',
        currentSystem: '',
        dataDescription: '',
        specialRequirements: '',
        preferredStartDate: '',
        primaryContact: {
          name: '',
          email: '',
          phone: ''
        },
        urgentMigration: false,
        onSiteTraining: false,
        weekendWork: false
      });
      
    } catch (error) {
      console.error('Error submitting order:', error);
      alert('There was an error submitting your order. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (currentStep === 1) {
    return (
      <div className="max-w-7xl mx-auto p-6">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold mb-4">
            Professional Data Migration Services
          </h1>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            Let our experts handle your transition to OneClass. Zero data loss, minimal disruption, 
            guaranteed success. Choose the package that fits your school's needs.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-12">
          {carePackages.map((pkg) => (
            <Card key={pkg.id} className={`relative overflow-hidden transition-all duration-300 hover:shadow-xl cursor-pointer ${
              pkg.badge === 'Best Value' ? 'ring-2 ring-green-500 scale-105' : ''
            }`} onClick={() => handlePackageSelect(pkg)}>
              {pkg.badge && (
                <div className={`absolute top-4 right-4 ${pkg.badgeColor} text-white px-3 py-1 rounded-full text-sm font-medium`}>
                  {pkg.badge}
                </div>
              )}
              
              <CardHeader className="pb-4">
                <CardTitle className="text-2xl">{pkg.name}</CardTitle>
                <CardDescription className="text-lg">{pkg.target}</CardDescription>
                
                <div className="mt-4">
                  <div className="text-4xl font-bold text-green-600">
                    ${pkg.price.toLocaleString()}
                  </div>
                  <div className="text-sm text-gray-500">
                    ~${calculateZWLPrice(pkg.price).toLocaleString()} ZWL
                  </div>
                </div>
                
                <div className="flex gap-4 text-sm text-gray-600 mt-4">
                  <div className="flex items-center gap-1">
                    <Clock className="h-4 w-4" />
                    {pkg.duration}
                  </div>
                  <div className="flex items-center gap-1">
                    <Users className="h-4 w-4" />
                    ROI: {pkg.roi}
                  </div>
                </div>
              </CardHeader>
              
              <CardContent>
                <div className="space-y-4">
                  <div>
                    <h4 className="font-semibold text-green-700 mb-2">✅ Included:</h4>
                    <ul className="space-y-2">
                      {pkg.features.slice(0, 4).map((feature, index) => (
                        <li key={index} className="flex items-start gap-2 text-sm">
                          <Check className="h-4 w-4 text-green-500 mt-0.5 flex-shrink-0" />
                          {feature}
                        </li>
                      ))}
                      {pkg.features.length > 4 && (
                        <li className="text-sm text-gray-500">
                          +{pkg.features.length - 4} more features...
                        </li>
                      )}
                    </ul>
                  </div>
                  
                  <div className="bg-blue-50 p-3 rounded-lg">
                    <div className="text-sm font-semibold text-blue-800">Value Proposition</div>
                    <div className="text-sm text-blue-700">{pkg.savings}</div>
                    <div className="text-xs text-blue-600">{pkg.value}</div>
                  </div>
                  
                  <Button className="w-full" size="lg">
                    Choose {pkg.name}
                    <ArrowRight className="h-4 w-4 ml-2" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        <div className="bg-gray-50 rounded-lg p-8 text-center">
          <h3 className="text-2xl font-bold mb-4">Why Choose Professional Migration?</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="flex flex-col items-center">
              <Shield className="h-12 w-12 text-green-500 mb-3" />
              <h4 className="font-semibold mb-2">95% Success Rate</h4>
              <p className="text-sm text-gray-600">Professional execution vs 40% DIY success rate</p>
            </div>
            <div className="flex flex-col items-center">
              <Clock className="h-12 w-12 text-blue-500 mb-3" />
              <h4 className="font-semibold mb-2">Save 200+ Hours</h4>
              <p className="text-sm text-gray-600">Expert team vs months of staff learning</p>
            </div>
            <div className="flex flex-col items-center">
              <Database className="h-12 w-12 text-purple-500 mb-3" />
              <h4 className="font-semibold mb-2">Zero Data Loss</h4>
              <p className="text-sm text-gray-600">Guaranteed data integrity and validation</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (currentStep === 2) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <div className="mb-8">
          <h2 className="text-3xl font-bold mb-2">Requirements Assessment</h2>
          <p className="text-gray-600">
            Help us understand your school's specific needs for the {selectedPackage?.name}
          </p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>School Information & Requirements</CardTitle>
            <CardDescription>
              This information helps us prepare for your migration and ensure smooth execution
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <Label htmlFor="studentCount">Current Number of Students</Label>
                <Input
                  id="studentCount"
                  type="number"
                  placeholder="e.g., 450"
                  value={requirements.studentCount}
                  onChange={(e) => setRequirements({...requirements, studentCount: e.target.value})}
                />
              </div>
              <div>
                <Label htmlFor="preferredStartDate">Preferred Start Date</Label>
                <Input
                  id="preferredStartDate"
                  type="date"
                  value={requirements.preferredStartDate}
                  onChange={(e) => setRequirements({...requirements, preferredStartDate: e.target.value})}
                />
              </div>
            </div>

            <div>
              <Label htmlFor="currentSystem">Current System Description</Label>
              <Textarea
                id="currentSystem"
                placeholder="Describe your current data management system (Excel files, paper records, existing software, etc.)"
                value={requirements.currentSystem}
                onChange={(e) => setRequirements({...requirements, currentSystem: e.target.value})}
                rows={3}
              />
            </div>

            <div>
              <Label htmlFor="dataDescription">Data Sources & History</Label>
              <Textarea
                id="dataDescription"
                placeholder="What data do you have? How many years of records? What format is it in?"
                value={requirements.dataDescription}
                onChange={(e) => setRequirements({...requirements, dataDescription: e.target.value})}
                rows={3}
              />
            </div>

            <div>
              <Label htmlFor="specialRequirements">Special Requirements or Concerns</Label>
              <Textarea
                id="specialRequirements"
                placeholder="Any specific requirements, integrations needed, concerns, or questions?"
                value={requirements.specialRequirements}
                onChange={(e) => setRequirements({...requirements, specialRequirements: e.target.value})}
                rows={3}
              />
            </div>

            <Separator />

            <div>
              <h4 className="font-semibold mb-3">Primary Contact Information</h4>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <Label htmlFor="contactName">Full Name</Label>
                  <Input
                    id="contactName"
                    placeholder="John Doe"
                    value={requirements.primaryContact.name}
                    onChange={(e) => setRequirements({
                      ...requirements,
                      primaryContact: {...requirements.primaryContact, name: e.target.value}
                    })}
                  />
                </div>
                <div>
                  <Label htmlFor="contactEmail">Email Address</Label>
                  <Input
                    id="contactEmail"
                    type="email"
                    placeholder="john@school.edu"
                    value={requirements.primaryContact.email}
                    onChange={(e) => setRequirements({
                      ...requirements,
                      primaryContact: {...requirements.primaryContact, email: e.target.value}
                    })}
                  />
                </div>
                <div>
                  <Label htmlFor="contactPhone">Phone Number</Label>
                  <Input
                    id="contactPhone"
                    placeholder="+263 77 123 4567"
                    value={requirements.primaryContact.phone}
                    onChange={(e) => setRequirements({
                      ...requirements,
                      primaryContact: {...requirements.primaryContact, phone: e.target.value}
                    })}
                  />
                </div>
              </div>
            </div>

            <Separator />

            <div>
              <h4 className="font-semibold mb-3">Additional Options</h4>
              <div className="space-y-3">
                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="urgentMigration"
                    checked={requirements.urgentMigration}
                    onCheckedChange={(checked) => setRequirements({...requirements, urgentMigration: checked})}
                  />
                  <Label htmlFor="urgentMigration">
                    Rush Migration (50% faster completion) - Additional $1,000
                  </Label>
                </div>
                
                {(selectedPackage?.id === 'growth' || selectedPackage?.id === 'enterprise') && (
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id="onSiteTraining"
                      checked={requirements.onSiteTraining}
                      onCheckedChange={(checked) => setRequirements({...requirements, onSiteTraining: checked})}
                    />
                    <Label htmlFor="onSiteTraining">
                      On-site Training (Recommended) - Additional $800
                    </Label>
                  </div>
                )}
                
                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="weekendWork"
                    checked={requirements.weekendWork}
                    onCheckedChange={(checked) => setRequirements({...requirements, weekendWork: checked})}
                  />
                  <Label htmlFor="weekendWork">
                    Weekend/Evening Work (Minimize school disruption) - Additional $500
                  </Label>
                </div>
              </div>
            </div>

            <div className="flex justify-between pt-6">
              <Button variant="outline" onClick={() => setCurrentStep(1)}>
                Back to Packages
              </Button>
              <Button onClick={handleRequirementsSubmit}>
                Continue to Payment
                <ArrowRight className="h-4 w-4 ml-2" />
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (currentStep === 3) {
    const basePrice = selectedPackage?.price || 0;
    const additionalCosts = 
      (requirements.urgentMigration ? 1000 : 0) +
      (requirements.onSiteTraining ? 800 : 0) +
      (requirements.weekendWork ? 500 : 0);
    const subtotal = basePrice + additionalCosts;
    const finalPrice = calculatePrice(subtotal, paymentOption);
    const savings = subtotal - finalPrice;

    return (
      <div className="max-w-4xl mx-auto p-6">
        <div className="mb-8">
          <h2 className="text-3xl font-bold mb-2">Order Summary & Payment</h2>
          <p className="text-gray-600">
            Review your order and choose your preferred payment method
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="lg:col-span-2 space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Payment Options</CardTitle>
                <CardDescription>Choose how you'd like to pay for your care package</CardDescription>
              </CardHeader>
              <CardContent>
                <RadioGroup value={paymentOption} onValueChange={setPaymentOption}>
                  {paymentOptions.map((option) => (
                    <div key={option.id} className="flex items-center space-x-2 p-4 border rounded-lg">
                      <RadioGroupItem value={option.id} id={option.id} />
                      <div className="flex-1">
                        <Label htmlFor={option.id} className="font-medium cursor-pointer">
                          {option.name}
                        </Label>
                        <p className="text-sm text-gray-500">{option.description}</p>
                        {option.discount > 0 && (
                          <Badge className="mt-1">Save {(option.discount * 100)}%</Badge>
                        )}
                      </div>
                    </div>
                  ))}
                </RadioGroup>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Terms & Conditions</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4 text-sm">
                <div className="flex items-center space-x-2">
                  <Checkbox id="terms" />
                  <Label htmlFor="terms">
                    I agree to the OneClass Migration Services Terms & Conditions
                  </Label>
                </div>
                <div className="flex items-center space-x-2">
                  <Checkbox id="guarantee" />
                  <Label htmlFor="guarantee">
                    I understand the performance guarantee and success criteria
                  </Label>
                </div>
                <div className="flex items-center space-x-2">
                  <Checkbox id="communication" />
                  <Label htmlFor="communication">
                    I consent to receive project updates via email and SMS
                  </Label>
                </div>
              </CardContent>
            </Card>
          </div>

          <div>
            <Card className="sticky top-6">
              <CardHeader>
                <CardTitle>Order Summary</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <h4 className="font-semibold">{selectedPackage?.name}</h4>
                  <p className="text-sm text-gray-500">{selectedPackage?.target}</p>
                  <div className="flex justify-between mt-2">
                    <span>Base Package</span>
                    <span>${basePrice.toLocaleString()}</span>
                  </div>
                </div>

                {additionalCosts > 0 && (
                  <div className="space-y-2">
                    <Separator />
                    <h5 className="font-medium text-sm">Additional Services:</h5>
                    {requirements.urgentMigration && (
                      <div className="flex justify-between text-sm">
                        <span>Rush Migration</span>
                        <span>$1,000</span>
                      </div>
                    )}
                    {requirements.onSiteTraining && (
                      <div className="flex justify-between text-sm">
                        <span>On-site Training</span>
                        <span>$800</span>
                      </div>
                    )}
                    {requirements.weekendWork && (
                      <div className="flex justify-between text-sm">
                        <span>Weekend Work</span>
                        <span>$500</span>
                      </div>
                    )}
                  </div>
                )}

                <Separator />
                
                <div className="flex justify-between">
                  <span>Subtotal</span>
                  <span>${subtotal.toLocaleString()}</span>
                </div>

                {savings > 0 && (
                  <div className="flex justify-between text-green-600">
                    <span>Discount (5%)</span>
                    <span>-${savings.toLocaleString()}</span>
                  </div>
                )}

                <Separator />
                
                <div className="flex justify-between text-lg font-bold">
                  <span>Total</span>
                  <span>${finalPrice.toLocaleString()}</span>
                </div>
                
                <div className="text-sm text-gray-500">
                  ~${calculateZWLPrice(finalPrice).toLocaleString()} ZWL
                </div>

                <div className="bg-blue-50 p-3 rounded-lg text-sm">
                  <div className="font-semibold text-blue-800">What happens next?</div>
                  <ol className="list-decimal list-inside text-blue-700 mt-1 space-y-1">
                    <li>Order confirmation email</li>
                    <li>Migration manager assigned</li>
                    <li>Project kickoff call</li>
                    <li>Data collection begins</li>
                  </ol>
                </div>

                <Button 
                  className="w-full" 
                  size="lg" 
                  onClick={handleOrderSubmit}
                  disabled={isSubmitting}
                >
                  {isSubmitting ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                      Submitting...
                    </>
                  ) : (
                    <>
                      <DollarSign className="h-4 w-4 mr-2" />
                      Submit Order
                    </>
                  )}
                </Button>

                <div className="flex justify-between pt-4">
                  <Button variant="outline" size="sm" onClick={() => setCurrentStep(2)}>
                    Back
                  </Button>
                  <Button variant="outline" size="sm" onClick={() => setCurrentStep(1)}>
                    Change Package
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    );
  }

  return null;
}