import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useLanguage } from '../contexts/LanguageContext';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Badge } from '../components/ui/badge';
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle } from '../components/ui/alert-dialog';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '../components/ui/dialog';
import { Label } from '../components/ui/label';
import { toast } from 'sonner';
import { ArrowLeft, Search, Edit, Trash2, Eye, Mail, Phone, MapPin, Upload, Plus } from 'lucide-react';
import EnhancedClientView from '../components/EnhancedClientView';
import axios from 'axios';

const API = process.env.REACT_APP_API_URL || '/api';

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
  const [deleteDialog, setDeleteDialog] = useState(false);
  const [clientToDelete, setClientToDelete] = useState(null);
  const [newClientDialog, setNewClientDialog] = useState(false);
  const [newClientData, setNewClientData] = useState({
    firstName: '',
    lastName: '',
    email: '',
    phone: '',
    country: '',
    caseType: ''
  });

  useEffect(() => {
    fetchClients();
  }, []);

  useEffect(() => {
    if (searchTerm) {
      const filtered = clients.filter(c =>
        c.firstName?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        c.lastName?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        c.email?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        c.clientNumber?.toLowerCase().includes(searchTerm.toLowerCase())
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

  const handleDelete = (client) => {
    setClientToDelete(client);
    setDeleteDialog(true);
  };

  const confirmDelete = async () => {
    if (!clientToDelete) return;
    
    try {
      await axios.delete(`${API}/admin/clients/${clientToDelete.clientNumber}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Client deleted successfully');
      fetchClients();
    } catch (error) {
      toast.error('Failed to delete client');
    } finally {
      setDeleteDialog(false);
      setClientToDelete(null);
    }
  };

  const handleCreateClient = async () => {
    try {
      await axios.post(`${API}/admin/clients`, newClientData, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Client created successfully');
      setNewClientDialog(false);
      fetchClients();
      // Reset form
      setNewClientData({ firstName: '', lastName: '', email: '', phone: '', country: '', caseType: '' });
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create client');
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
            <div className="flex space-x-4">
              <div className="relative flex-grow">
                <Search className="absolute left-3 top-3 w-5 h-5 text-gray-400" />
                <Input
                  placeholder={language === 'de' ? 'Suchen...' : 'Search...'}
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
              <Button onClick={() => setNewClientDialog(true)}>
                <Plus className="w-4 h-4 mr-2" />
                New Client
              </Button>
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
                      <Button
                        size="sm"
                        className="bg-purple-600 hover:bg-purple-700 text-white"
                        onClick={() => navigate(`/admin/data-collection?clientNumber=${client.clientNumber}`)}
                      >
                        <Upload className="w-4 h-4 mr-1" />
                        Veri Topla
                      </Button>
                      <Button size="sm" variant="outline" onClick={() => handleDelete(client)}>
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

      {/* Enhanced Client View */}
      {viewDialog && selectedClient && (
        <EnhancedClientView
          clientData={selectedClient}
          onClose={() => setViewDialog(false)}
          token={token}
        />
      )}

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

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={deleteDialog} onOpenChange={setDeleteDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Are you sure?</AlertDialogTitle>
            <AlertDialogDescription>
              This action cannot be undone. This will mark the client as 'deleted' but will not permanently remove their data.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={confirmDelete}>Continue</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* New Client Dialog */}
      <Dialog open={newClientDialog} onOpenChange={setNewClientDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Create New Client</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="grid grid-cols-2 gap-4">
              <Input placeholder="First Name" value={newClientData.firstName} onChange={(e) => setNewClientData({...newClientData, firstName: e.target.value})} />
              <Input placeholder="Last Name" value={newClientData.lastName} onChange={(e) => setNewClientData({...newClientData, lastName: e.target.value})} />
            </div>
            <Input placeholder="Email" type="email" value={newClientData.email} onChange={(e) => setNewClientData({...newClientData, email: e.target.value})} />
            <Input placeholder="Phone" value={newClientData.phone} onChange={(e) => setNewClientData({...newClientData, phone: e.target.value})} />
            <Input placeholder="Country" value={newClientData.country} onChange={(e) => setNewClientData({...newClientData, country: e.target.value})} />
            <Input placeholder="Case Type" value={newClientData.caseType} onChange={(e) => setNewClientData({...newClientData, caseType: e.target.value})} />
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setNewClientDialog(false)}>Cancel</Button>
            <Button onClick={handleCreateClient}>Create Client</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default AdminClients;
