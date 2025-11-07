"""
Contact Network Analyzer
Analyzes communication patterns and contact relationships
"""

from typing import Dict, List
from collections import defaultdict

class ContactNetworkAnalyzer:
    """Analyze contact network and communication patterns"""
    
    async def analyze_network(
        self,
        whatsapp_data: Dict,
        telegram_data: Dict,
        sms_data: Dict,
        signal_data: Dict
    ) -> Dict:
        """
        Analyze contact network across all platforms
        
        Returns:
            Network analysis with frequency, relationships, etc.
        """
        contacts = defaultdict(lambda: {
            "name": None,
            "identifiers": set(),
            "platforms": set(),
            "message_count": 0,
            "call_count": 0,
            "last_contact": None,
            "first_contact": None
        })
        
        # Process WhatsApp contacts
        for msg in whatsapp_data.get("messages", []):
            contact = msg.get("contact")
            if contact:
                contacts[contact]["identifiers"].add(contact)
                contacts[contact]["platforms"].add("WhatsApp")
                contacts[contact]["message_count"] += 1
                self._update_timestamps(contacts[contact], msg.get("timestamp"))
        
        # Process Telegram contacts
        for msg in telegram_data.get("messages", []):
            user_id = str(msg.get("user_id"))
            if user_id:
                contacts[user_id]["identifiers"].add(user_id)
                contacts[user_id]["platforms"].add("Telegram")
                contacts[user_id]["message_count"] += 1
                self._update_timestamps(contacts[user_id], msg.get("timestamp"))
        
        # Add contact names from Telegram
        for contact in telegram_data.get("contacts", []):
            contact_id = str(contact.get("id"))
            if contact_id in contacts:
                contacts[contact_id]["name"] = contact.get("name")
        
        # Process SMS
        for msg in sms_data.get("messages", []):
            address = msg.get("address")
            if address:
                contacts[address]["identifiers"].add(address)
                contacts[address]["platforms"].add("SMS")
                contacts[address]["message_count"] += 1
                self._update_timestamps(contacts[address], msg.get("timestamp"))
        
        # Process Calls
        for call in sms_data.get("calls", []):
            number = call.get("number")
            if number:
                contacts[number]["identifiers"].add(number)
                contacts[number]["platforms"].add("Phone")
                contacts[number]["call_count"] += 1
                contacts[number]["name"] = call.get("name") or contacts[number]["name"]
                self._update_timestamps(contacts[number], call.get("timestamp"))
        
        # Process Signal
        for msg in signal_data.get("messages", []):
            address = msg.get("address")
            if address:
                contacts[address]["identifiers"].add(address)
                contacts[address]["platforms"].add("Signal")
                contacts[address]["message_count"] += 1
                self._update_timestamps(contacts[address], msg.get("date_sent"))
        
        # Convert to serializable format
        network = {}
        for contact_id, data in contacts.items():
            network[contact_id] = {
                "name": data["name"],
                "identifiers": list(data["identifiers"]),
                "platforms": list(data["platforms"]),
                "message_count": data["message_count"],
                "call_count": data["call_count"],
                "last_contact": data["last_contact"],
                "first_contact": data["first_contact"],
                "total_interactions": data["message_count"] + data["call_count"]
            }
        
        # Sort by total interactions
        sorted_contacts = sorted(
            network.items(),
            key=lambda x: x[1]["total_interactions"],
            reverse=True
        )
        
        return {
            "total_contacts": len(network),
            "contacts": dict(sorted_contacts[:100]),  # Top 100 contacts
            "top_contacts": [c[0] for c in sorted_contacts[:10]],  # Top 10
            "platform_distribution": self._count_platforms(network)
        }
    
    def _update_timestamps(self, contact_data: Dict, timestamp):
        """Update first and last contact timestamps"""
        if timestamp:
            if contact_data["last_contact"] is None or timestamp > contact_data["last_contact"]:
                contact_data["last_contact"] = timestamp
            if contact_data["first_contact"] is None or timestamp < contact_data["first_contact"]:
                contact_data["first_contact"] = timestamp
    
    def _count_platforms(self, network: Dict) -> Dict:
        """Count contacts by platform"""
        platform_counts = defaultdict(int)
        
        for contact_data in network.values():
            for platform in contact_data.get("platforms", []):
                platform_counts[platform] += 1
        
        return dict(platform_counts)
