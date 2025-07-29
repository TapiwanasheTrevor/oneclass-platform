"use client"

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { School, Search, ExternalLink, Building } from 'lucide-react';
import { buildSchoolUrl, isValidSubdomain } from '@/utils/subdomain';

interface SchoolInfo {
  id: string;
  name: string;
  subdomain: string;
  type: string;
  status: string;
}

export default function SchoolSelector() {
  const [schools, setSchools] = useState<SchoolInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [subdomainInput, setSubdomainInput] = useState('');

  useEffect(() => {
    fetchSchools();
  }, []);

  const fetchSchools = async () => {
    try {
      const response = await fetch('/api/v1/platform/schools/public');
      if (response.ok) {
        const data = await response.json();
        setSchools(data);
      }
    } catch (error) {
      console.error('Error fetching schools:', error);
    } finally {
      setLoading(false);
    }
  };

  const filteredSchools = schools.filter(school =>
    school.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    school.subdomain.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleSchoolAccess = (subdomain: string) => {
    const url = buildSchoolUrl(subdomain, '/login');
    window.open(url, '_blank');
  };

  const handleDirectAccess = () => {
    if (isValidSubdomain(subdomainInput)) {
      const url = buildSchoolUrl(subdomainInput, '/login');
      window.open(url, '_blank');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center space-y-4">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="text-lg font-medium text-gray-900">Loading Schools...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-12">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-12">
          <div className="flex justify-center mb-4">
            <School className="h-16 w-16 text-blue-600" />
          </div>
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            Welcome to OneClass
          </h1>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto">
            Access your school's OneClass platform. Each school has its own dedicated subdomain for secure, isolated access.
          </p>
        </div>

        {/* Direct Access */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <ExternalLink className="h-5 w-5" />
              Direct Access
            </CardTitle>
            <CardDescription>
              If you know your school's subdomain, enter it below for direct access.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex gap-4">
              <div className="flex-1">
                <Label htmlFor="subdomain">School Subdomain</Label>
                <div className="flex mt-1">
                  <Input
                    id="subdomain"
                    placeholder="palm-springs-jnr"
                    value={subdomainInput}
                    onChange={(e) => setSubdomainInput(e.target.value)}
                    className="rounded-r-none"
                  />
                  <div className="px-3 py-2 bg-gray-100 border border-l-0 rounded-r-md text-sm text-gray-600">
                    .oneclass.local:3000
                  </div>
                </div>
              </div>
              <div className="flex items-end">
                <Button 
                  onClick={handleDirectAccess}
                  disabled={!isValidSubdomain(subdomainInput)}
                >
                  Access School
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* School Search */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Search className="h-5 w-5" />
              Find Your School
            </CardTitle>
            <CardDescription>
              Search for your school from our directory.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="mb-6">
              <Label htmlFor="search">Search Schools</Label>
              <Input
                id="search"
                placeholder="Search by school name or subdomain..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="mt-1"
              />
            </div>

            {/* Schools Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {filteredSchools.map((school) => (
                <Card key={school.id} className="hover:shadow-md transition-shadow">
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex items-center gap-2">
                        <Building className="h-5 w-5 text-blue-600" />
                        <span className="text-sm font-medium text-blue-600 capitalize">
                          {school.type}
                        </span>
                      </div>
                      <span className={`px-2 py-1 text-xs rounded-full ${
                        school.status === 'active' 
                          ? 'bg-green-100 text-green-800' 
                          : 'bg-gray-100 text-gray-800'
                      }`}>
                        {school.status}
                      </span>
                    </div>
                    
                    <h3 className="font-semibold text-gray-900 mb-2">
                      {school.name}
                    </h3>
                    
                    <p className="text-sm text-gray-600 mb-4">
                      {school.subdomain}.oneclass.local
                    </p>
                    
                    <Button 
                      onClick={() => handleSchoolAccess(school.subdomain)}
                      className="w-full"
                      size="sm"
                    >
                      Access School
                    </Button>
                  </CardContent>
                </Card>
              ))}
            </div>

            {filteredSchools.length === 0 && searchTerm && (
              <div className="text-center py-8">
                <p className="text-gray-500">No schools found matching "{searchTerm}"</p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Instructions */}
        <Card>
          <CardHeader>
            <CardTitle>How It Works</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4 text-sm text-gray-600">
              <div className="flex gap-3">
                <span className="flex-shrink-0 w-6 h-6 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-xs font-semibold">1</span>
                <p>Each school has its own dedicated subdomain (e.g., palm-springs-jnr.oneclass.local)</p>
              </div>
              <div className="flex gap-3">
                <span className="flex-shrink-0 w-6 h-6 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-xs font-semibold">2</span>
                <p>Access your school by clicking "Access School" or entering the subdomain directly</p>
              </div>
              <div className="flex gap-3">
                <span className="flex-shrink-0 w-6 h-6 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-xs font-semibold">3</span>
                <p>Log in with your school credentials on your school's dedicated platform</p>
              </div>
              <div className="flex gap-3">
                <span className="flex-shrink-0 w-6 h-6 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-xs font-semibold">4</span>
                <p>Your data is completely isolated and secure within your school's environment</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
