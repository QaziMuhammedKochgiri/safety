import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useLanguage } from '../contexts/LanguageContext';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Badge } from '../components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '../components/ui/dialog';
import { Label } from '../components/ui/label';
import { toast } from 'sonner';
import { ArrowLeft, Search, Edit, Trash2, Eye, Mail, Phone, MapPin } from 'lucide-react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const AdminClients = () => {
  const { language } = useLanguage();
  const { token } = useAuth();
  const navigate = useNavigate();
  const [clients, setClients] = useState([]);
  const [filteredClients, setFilteredClients] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedClient, setSelectedClient] = useState(null);
  const [viewDialog, setViewDialog] = useState(false);
  const [editDialog, setEditDialog] = useState(false);
  const [editData, setEditData] = useState({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchClients();
  }, []);

  useEffect(() => {
    if (searchTerm) {
      const filtered = clients.filter(c => 
        c.firstName.toLowerCase().includes(searchTerm.toLowerCase()) ||
        c.lastName.toLowerCase().includes(searchTerm.toLowerCase()) ||
        c.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
        c.clientNumber.toLowerCase().includes(searchTerm.toLowerCase())
      );
      setFilteredClients(filtered);
    } else {
      setFilteredClients(clients);
    }
  }, [searchTerm, clients]);

  const fetchClients = async () => {
    try {
      const response = await axios.get(`${API}/admin/clients`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setClients(response.data.clients.filter(c => c.role !== 'admin'));
      setFilteredClients(response.data.clients.filter(c => c.role !== 'admin'));
    } catch (error) {
      toast.error('Failed to load clients');
    } finally {
      setLoading(false);
    }
  };

  const handleView = async (clientNumber) => {
    try {
      const response = await axios.get(`${API}/admin/clients/${clientNumber}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSelectedClient(response.data);
      setViewDialog(true);
    } catch (error) {
      toast.error('Failed to load client details');
    }
  };

  const handleEdit = (client) => {
    setEditData({ 
      firstName: client.firstName,
      lastName: client.lastName,
      phone: client.phone,
      country: client.country,
      status: client.status
    });
    setSelectedClient(client);
    setEditDialog(true);
  };

  const handleUpdate = async () => {
    try {
      await axios.put(`${API}/admin/clients/${selectedClient.clientNumber}`, editData, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Client updated successfully');
      setEditDialog(false);
      fetchClients();
    } catch (error) {
      toast.error('Failed to update client');
    }
  };

  const handleDelete = async (clientNumber) => {
    if (!window.confirm('Are you sure you want to delete this client?')) return;
    
    try {
      await axios.delete(`${API}/admin/clients/${clientNumber}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Client deleted successfully');
      fetchClients();
    } catch (error) {
      toast.error('Failed to delete client');
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="bg-white border-b">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center space-x-4">
            <Button variant="ghost" onClick={() => navigate('/admin')}>
              <ArrowLeft className="w-4 h-4 mr-2" />
              {language === 'de' ? 'Zurück' : 'Back'}
            </Button>
            <h1 className="text-2xl font-bold">
              {language === 'de' ? 'Mandanten verwalten' : 'Manage Clients'}
            </h1>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 py-8">
        <Card className="mb-6">
          <CardContent className="p-4">
            <div className="relative">
              <Search className="absolute left-3 top-3 w-5 h-5 text-gray-400" />
              <Input
                placeholder={language === 'de' ? 'Suchen...' : 'Search...'}
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
          </CardContent>
        </Card>

        {loading ? (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          </div>
        ) : (
          <div className="grid gap-4">
            {filteredClients.map((client) => (
              <Card key={client.clientNumber} className="hover:shadow-lg transition-shadow">
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-3 mb-2">
                        <h3 className="text-xl font-bold">{client.firstName} {client.lastName}</h3>
                        <Badge variant={client.status === 'active' ? 'default' : 'secondary'}>
                          {client.status}
                        </Badge>
                      </div>
                      <div className="grid md:grid-cols-2 gap-2 text-sm text-gray-600">
                        <div className="flex items-center space-x-2">
                          <Mail className="w-4 h-4" />
                          <span>{client.email}</span>
                        </div>
                        <div className="flex items-center space-x-2">
                          <Phone className="w-4 h-4" />
                          <span>{client.phone}</span>
                        </div>
                        <div className="flex items-center space-x-2">
                          <MapPin className="w-4 h-4" />
                          <span>{client.country}</span>
                        </div>
                        <div className="font-mono text-xs bg-gray-100 px-2 py-1 rounded">
                          {client.clientNumber}
                        </div>
                      </div>
                    </div>
                    <div className="flex space-x-2">
                      <Button size="sm" variant="outline" onClick={() => handleView(client.clientNumber)}>
                        <Eye className="w-4 h-4" />
                      </Button>
                      <Button size="sm" variant="outline" onClick={() => handleEdit(client)}>
                        <Edit className="w-4 h-4" />
                      </Button>
                      <Button size="sm" variant="outline" onClick={() => handleDelete(client.clientNumber)}>
                        <Trash2 className="w-4 h-4 text-red-600" />
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>

      {/* View Dialog */}
      <Dialog open={viewDialog} onOpenChange={setViewDialog}>
        <DialogContent className="max-w-3xl">
          <DialogHeader>
            <DialogTitle>Client Details</DialogTitle>
          </DialogHeader>
          {selectedClient && (
            <div className="space-y-4">
              <div className="grid md:grid-cols-2 gap-4">
                <div>
                  <Label>Name</Label>
                  <p className="font-medium">{selectedClient.client.firstName} {selectedClient.client.lastName}</p>
                </div>
                <div>
                  <Label>Email</Label>
                  <p className="font-medium">{selectedClient.client.email}</p>
                </div>
              </div>
              <div>
                <Label>Documents ({selectedClient.documents.length})</Label>
                <div className="mt-2 space-y-2">
                  {selectedClient.documents.map(doc => (
                    <div key={doc.documentNumber} className="text-sm p-2 bg-gray-50 rounded">
                      {doc.fileName}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Edit Dialog */}
      <Dialog open={editDialog} onOpenChange={setEditDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Edit Client</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label>First Name</Label>
              <Input value={editData.firstName || ''} onChange={(e) => setEditData({...editData, firstName: e.target.value})} />
            </div>
            <div>
              <Label>Last Name</Label>
              <Input value={editData.lastName || ''} onChange={(e) => setEditData({...editData, lastName: e.target.value})} />
            </div>
            <div>
              <Label>Phone</Label>
              <Input value={editData.phone || ''} onChange={(e) => setEditData({...editData, phone: e.target.value})} />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setEditDialog(false)}>Cancel</Button>
            <Button onClick={handleUpdate}>Update</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default AdminClients;
