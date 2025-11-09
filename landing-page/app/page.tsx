'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import MapSelector from '@/components/map-selector';
import { Sun, Zap, TrendingDown, MapPin, CheckCircle2 } from 'lucide-react';

interface FormData {
  nom: string;
  prenom: string;
  email: string;
  telephone: string;
  factureElectricite: string;
  latitude: number | null;
  longitude: number | null;
}

export default function SolarLandingPage() {
  const [formData, setFormData] = useState<FormData>({
    nom: '',
    prenom: '',
    email: '',
    telephone: '',
    factureElectricite: '',
    latitude: null,
    longitude: null,
  });

  const [position, setPosition] = useState<[number, number] | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handlePositionChange = (lat: number, lng: number) => {
    setPosition([lat, lng]);
    setFormData(prev => ({ ...prev, latitude: lat, longitude: lng }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setError(null);

    // Validation
    if (!formData.nom || !formData.prenom || !formData.email || !formData.telephone || !formData.factureElectricite) {
      setError('Veuillez remplir tous les champs');
      setIsSubmitting(false);
      return;
    }

    if (!formData.latitude || !formData.longitude) {
      setError('Veuillez sélectionner l\'emplacement de votre toiture sur la carte');
      setIsSubmitting(false);
      return;
    }

    try {
      const response = await fetch('https://n8n.energum.earth/webhook/dfb660da-1480-40a5-bbdc-7579e6772fe1', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          nom: formData.nom,
          prenom: formData.prenom,
          email: formData.email,
          telephone: formData.telephone,
          facture_mensuelle_electricite: formData.factureElectricite,
          coordonnees_gps: {
            latitude: formData.latitude,
            longitude: formData.longitude,
          },
          date_soumission: new Date().toISOString(),
        }),
      });

      if (response.ok) {
        setIsSuccess(true);
        // Réinitialiser le formulaire
        setFormData({
          nom: '',
          prenom: '',
          email: '',
          telephone: '',
          factureElectricite: '',
          latitude: null,
          longitude: null,
        });
        setPosition(null);
      } else {
        throw new Error('Erreur lors de l\'envoi');
      }
    } catch (err) {
      setError('Une erreur est survenue. Veuillez réessayer.');
      console.error(err);
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isSuccess) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-orange-50 flex items-center justify-center p-4">
        <Card className="max-w-md w-full text-center">
          <CardHeader>
            <div className="mx-auto mb-4 w-16 h-16 bg-green-100 rounded-full flex items-center justify-center">
              <CheckCircle2 className="w-10 h-10 text-green-600" />
            </div>
            <CardTitle className="text-2xl">Merci !</CardTitle>
            <CardDescription>
              Votre demande a été envoyée avec succès. Nous vous contacterons rapidement pour étudier votre projet solaire.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button onClick={() => setIsSuccess(false)} className="w-full">
              Faire une nouvelle demande
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-orange-50">
      {/* Hero Section */}
      <div className="container mx-auto px-4 py-12">
        <div className="text-center mb-12">
          <div className="inline-flex items-center gap-2 mb-4">
            <Sun className="w-12 h-12 text-orange-500" />
            <h1 className="text-5xl font-bold bg-gradient-to-r from-blue-600 to-orange-500 bg-clip-text text-transparent">
              Passez au Solaire
            </h1>
          </div>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto">
            Réduisez vos factures d'électricité jusqu'à 70% avec une installation photovoltaïque sur mesure
          </p>
        </div>

        {/* Features */}
        <div className="grid md:grid-cols-3 gap-6 mb-12">
          <Card className="text-center">
            <CardHeader>
              <Zap className="w-12 h-12 text-yellow-500 mx-auto mb-2" />
              <CardTitle className="text-lg">Économies Immédiates</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-gray-600">
                Produisez votre propre électricité et réduisez vos factures dès le premier jour
              </p>
            </CardContent>
          </Card>

          <Card className="text-center">
            <CardHeader>
              <TrendingDown className="w-12 h-12 text-green-500 mx-auto mb-2" />
              <CardTitle className="text-lg">Rentable à long terme</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-gray-600">
                Amortissement rapide et revenus garantis pendant 20 ans minimum
              </p>
            </CardContent>
          </Card>

          <Card className="text-center">
            <CardHeader>
              <Sun className="w-12 h-12 text-orange-500 mx-auto mb-2" />
              <CardTitle className="text-lg">Énergie Propre</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-gray-600">
                Contribuez à la transition énergétique et à la protection de l'environnement
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Form */}
        <Card className="max-w-4xl mx-auto">
          <CardHeader>
            <CardTitle className="text-2xl">Obtenez votre étude gratuite</CardTitle>
            <CardDescription>
              Remplissez le formulaire ci-dessous et recevez une estimation personnalisée sous 24h
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-6">
              {error && (
                <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded-md">
                  {error}
                </div>
              )}

              <div className="grid md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="nom">Nom *</Label>
                  <Input
                    id="nom"
                    name="nom"
                    value={formData.nom}
                    onChange={handleInputChange}
                    placeholder="Votre nom"
                    required
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="prenom">Prénom *</Label>
                  <Input
                    id="prenom"
                    name="prenom"
                    value={formData.prenom}
                    onChange={handleInputChange}
                    placeholder="Votre prénom"
                    required
                  />
                </div>
              </div>

              <div className="grid md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="email">Email *</Label>
                  <Input
                    id="email"
                    name="email"
                    type="email"
                    value={formData.email}
                    onChange={handleInputChange}
                    placeholder="votre@email.fr"
                    required
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="telephone">Téléphone *</Label>
                  <Input
                    id="telephone"
                    name="telephone"
                    type="tel"
                    value={formData.telephone}
                    onChange={handleInputChange}
                    placeholder="06 12 34 56 78"
                    required
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="factureElectricite">Facture mensuelle d'électricité (€) *</Label>
                <Input
                  id="factureElectricite"
                  name="factureElectricite"
                  type="number"
                  value={formData.factureElectricite}
                  onChange={handleInputChange}
                  placeholder="150"
                  required
                />
              </div>

              <div className="space-y-2">
                <Label className="flex items-center gap-2">
                  <MapPin className="w-4 h-4" />
                  Emplacement de votre toiture *
                </Label>
                <p className="text-sm text-gray-600 mb-2">
                  Cliquez sur la carte pour indiquer l'emplacement exact de votre toiture
                </p>
                <MapSelector position={position} onPositionChange={handlePositionChange} />
                {position && (
                  <p className="text-sm text-green-600 mt-2">
                    ✓ Position sélectionnée: {position[0].toFixed(6)}, {position[1].toFixed(6)}
                  </p>
                )}
              </div>

              <Button type="submit" className="w-full text-lg h-12" disabled={isSubmitting}>
                {isSubmitting ? 'Envoi en cours...' : 'Obtenir mon étude gratuite'}
              </Button>

              <p className="text-xs text-gray-500 text-center">
                En soumettant ce formulaire, vous acceptez d'être contacté par nos conseillers pour votre projet solaire.
              </p>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
