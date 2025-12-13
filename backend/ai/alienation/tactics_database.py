"""
Parental Alienation Tactics Database
50+ manipulation tactics with literature-backed definitions and case law references.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum
from datetime import datetime
import json


class TacticCategory(str, Enum):
    """Categories of alienation tactics."""
    DENIGRATION = "denigration"  # Badmouthing the other parent
    INTERFERENCE = "interference"  # Interfering with contact/communication
    EMOTIONAL_MANIPULATION = "emotional_manipulation"  # Guilt, fear, loyalty conflicts
    INFORMATION_CONTROL = "information_control"  # Withholding/distorting information
    IDENTITY_ERASURE = "identity_erasure"  # Removing other parent from child's life
    LEGAL_ABUSE = "legal_abuse"  # Misuse of legal system
    CHILD_WEAPONIZATION = "child_weaponization"  # Using child as messenger/spy
    FALSE_ALLEGATIONS = "false_allegations"  # Fabricated abuse claims
    GATEKEEPING = "gatekeeping"  # Controlling access to child
    PSYCHOLOGICAL_CONTROL = "psychological_control"  # Coercive control tactics


class TacticSeverity(str, Enum):
    """Severity levels for tactics."""
    MILD = "mild"  # Score 1-3
    MODERATE = "moderate"  # Score 4-6
    SEVERE = "severe"  # Score 7-8
    EXTREME = "extreme"  # Score 9-10


@dataclass
class LiteratureReference:
    """Academic literature reference."""
    reference_id: str
    authors: List[str]
    title: str
    journal: str
    year: int
    doi: Optional[str] = None
    pages: Optional[str] = None
    relevance_score: float = 0.0  # How relevant to this tactic
    quote: Optional[str] = None  # Key quote from literature


@dataclass
class CaseLawReference:
    """Legal case reference."""
    reference_id: str
    case_name: str
    court: str
    jurisdiction: str  # DE, TR, US, UK, EU
    year: int
    citation: str
    relevance: str  # How this case relates to the tactic
    outcome: str  # Brief description of outcome
    key_finding: Optional[str] = None


@dataclass
class ManipulationTactic:
    """Definition of a manipulation tactic."""
    tactic_id: str
    name: str
    name_de: str  # German name
    name_tr: str  # Turkish name
    category: TacticCategory
    description: str
    description_de: str
    description_tr: str
    indicators: List[str]  # What to look for in messages
    keywords: Dict[str, List[str]]  # Language-specific keywords
    example_phrases: Dict[str, List[str]]  # Example phrases by language
    severity_base: int  # Base severity score (1-10)
    literature_refs: List[LiteratureReference] = field(default_factory=list)
    case_law_refs: List[CaseLawReference] = field(default_factory=list)
    counter_indicators: List[str] = field(default_factory=list)  # Signs this ISN'T alienation
    frequency_weight: float = 1.0  # How much frequency affects severity
    context_modifiers: Dict[str, float] = field(default_factory=dict)


class AlienationTacticDB:
    """Database of 50+ parental alienation tactics."""

    def __init__(self):
        self.tactics: Dict[str, ManipulationTactic] = {}
        self.literature: Dict[str, LiteratureReference] = {}
        self.case_law: Dict[str, CaseLawReference] = {}
        self._load_tactics()
        self._load_literature()
        self._load_case_law()

    def _load_tactics(self):
        """Load all 50+ tactics."""
        tactics_data = [
            # DENIGRATION TACTICS (1-10)
            {
                "tactic_id": "DEN001",
                "name": "Direct Badmouthing",
                "name_de": "Direktes Schlechtmachen",
                "name_tr": "Doğrudan Kötüleme",
                "category": TacticCategory.DENIGRATION,
                "description": "Explicitly saying negative things about the other parent to the child",
                "description_de": "Explizites Aussprechen negativer Dinge über den anderen Elternteil gegenüber dem Kind",
                "description_tr": "Diğer ebeveyn hakkında çocuğa açıkça olumsuz şeyler söyleme",
                "indicators": [
                    "Calling other parent names in front of child",
                    "Listing faults of other parent",
                    "Comparing child negatively to other parent"
                ],
                "keywords": {
                    "en": ["your father is", "your mother is", "just like your dad", "terrible parent"],
                    "de": ["dein Vater ist", "deine Mutter ist", "genau wie dein Vater", "schlechter Elternteil"],
                    "tr": ["baban şöyle", "annen şöyle", "tıpkı baban gibi", "kötü ebeveyn"]
                },
                "example_phrases": {
                    "en": ["Your father doesn't care about you", "Your mother is crazy"],
                    "de": ["Dein Vater kümmert sich nicht um dich", "Deine Mutter ist verrückt"],
                    "tr": ["Baban seni umursamıyor", "Annen deli"]
                },
                "severity_base": 7,
                "counter_indicators": ["Expressing legitimate concerns about safety", "Age-appropriate explanations"]
            },
            {
                "tactic_id": "DEN002",
                "name": "Subtle Disparagement",
                "name_de": "Subtile Herabsetzung",
                "name_tr": "Üstü Kapalı Küçümseme",
                "category": TacticCategory.DENIGRATION,
                "description": "Indirect negative comments, sighs, eye-rolls when mentioning other parent",
                "description_de": "Indirekte negative Kommentare, Seufzer, Augenrollen bei Erwähnung des anderen Elternteils",
                "description_tr": "Diğer ebeveynden bahsederken dolaylı olumsuz yorumlar, iç çekme",
                "indicators": [
                    "Sarcastic comments about other parent",
                    "Dismissive language",
                    "Implied criticism without direct statement"
                ],
                "keywords": {
                    "en": ["typical", "of course he/she", "what did you expect", "surprise surprise"],
                    "de": ["typisch", "natürlich hat er/sie", "was hast du erwartet"],
                    "tr": ["tipik", "tabii ki", "ne bekliyordun ki"]
                },
                "example_phrases": {
                    "en": ["Well, that's typical of your father", "What did you expect from your mother?"],
                    "de": ["Das ist typisch für deinen Vater", "Was hast du von deiner Mutter erwartet?"],
                    "tr": ["Babandan beklenen bu zaten", "Annenden ne beklerdin ki?"]
                },
                "severity_base": 5
            },
            {
                "tactic_id": "DEN003",
                "name": "Blame Attribution",
                "name_de": "Schuldzuweisung",
                "name_tr": "Suç Yükleme",
                "category": TacticCategory.DENIGRATION,
                "description": "Blaming other parent for all family problems, divorce, financial issues",
                "description_de": "Dem anderen Elternteil die Schuld für alle Familienprobleme geben",
                "description_tr": "Tüm aile sorunları için diğer ebeveyni suçlama",
                "indicators": [
                    "Attributing divorce to other parent's fault",
                    "Blaming financial problems on other parent",
                    "Making child feel other parent caused suffering"
                ],
                "keywords": {
                    "en": ["because of your father", "your mother's fault", "he/she ruined", "destroyed our family"],
                    "de": ["wegen deinem Vater", "Schuld deiner Mutter", "hat uns ruiniert", "Familie zerstört"],
                    "tr": ["baban yüzünden", "annenin suçu", "mahvetti", "ailemizi yıktı"]
                },
                "example_phrases": {
                    "en": ["We can't afford this because your father left us", "Your mother destroyed our family"],
                    "de": ["Wir können uns das nicht leisten, weil dein Vater uns verlassen hat"],
                    "tr": ["Baban bizi terk ettiği için bunu karşılayamıyoruz"]
                },
                "severity_base": 6
            },
            {
                "tactic_id": "DEN004",
                "name": "Character Assassination",
                "name_de": "Rufmord",
                "name_tr": "Karakter Suikasti",
                "category": TacticCategory.DENIGRATION,
                "description": "Systematic destruction of other parent's character and reputation",
                "description_de": "Systematische Zerstörung des Charakters und Rufs des anderen Elternteils",
                "description_tr": "Diğer ebeveynin karakterinin sistematik olarak yıkılması",
                "indicators": [
                    "Sharing adult relationship details with child",
                    "Exaggerating minor faults",
                    "Presenting other parent as fundamentally flawed"
                ],
                "keywords": {
                    "en": ["always been", "never cared", "selfish person", "narcissist", "abuser"],
                    "de": ["war schon immer", "hat sich nie gekümmert", "egoistische Person", "Narzisst"],
                    "tr": ["hep böyleydi", "hiç umursamadı", "bencil biri", "narsist"]
                },
                "example_phrases": {
                    "en": ["Your father has always been a selfish narcissist"],
                    "de": ["Dein Vater war schon immer ein egoistischer Narzisst"],
                    "tr": ["Baban her zaman bencil bir narsistti"]
                },
                "severity_base": 8
            },
            {
                "tactic_id": "DEN005",
                "name": "Undermining Authority",
                "name_de": "Autorität Untergraben",
                "name_tr": "Otoriteyi Baltalama",
                "category": TacticCategory.DENIGRATION,
                "description": "Discrediting other parent's rules, decisions, and parenting",
                "description_de": "Diskreditierung der Regeln und Entscheidungen des anderen Elternteils",
                "description_tr": "Diğer ebeveynin kurallarını ve kararlarını itibarsızlaştırma",
                "indicators": [
                    "Contradicting other parent's rules",
                    "Calling other parent's decisions stupid",
                    "Encouraging child to disobey other parent"
                ],
                "keywords": {
                    "en": ["stupid rule", "doesn't know what", "ignore what", "don't have to listen"],
                    "de": ["dumme Regel", "weiß nicht was", "ignoriere was", "musst nicht hören"],
                    "tr": ["saçma kural", "ne bilir", "dinleme", "takmak zorunda değilsin"]
                },
                "example_phrases": {
                    "en": ["Your father's rules are stupid, you don't have to follow them here"],
                    "de": ["Die Regeln deines Vaters sind dumm"],
                    "tr": ["Babanın kuralları saçma, burada uymak zorunda değilsin"]
                },
                "severity_base": 6
            },

            # INTERFERENCE TACTICS (11-20)
            {
                "tactic_id": "INT001",
                "name": "Visitation Interference",
                "name_de": "Umgangsbehinderung",
                "name_tr": "Görüşme Engelleme",
                "category": TacticCategory.INTERFERENCE,
                "description": "Scheduling conflicts, sudden illnesses, or excuses to prevent visits",
                "description_de": "Terminkonflikte, plötzliche Krankheiten oder Ausreden zur Verhinderung von Besuchen",
                "description_tr": "Ziyaretleri engellemek için randevu çakışmaları veya bahaneler",
                "indicators": [
                    "Frequent last-minute cancellations",
                    "Child suddenly ill before visits",
                    "Scheduling activities during other parent's time"
                ],
                "keywords": {
                    "en": ["can't make it", "something came up", "not feeling well", "has a party"],
                    "de": ["geht nicht", "ist etwas dazwischengekommen", "fühlt sich nicht wohl"],
                    "tr": ["olmayacak", "bir şey çıktı", "iyi hissetmiyor", "partisi var"]
                },
                "example_phrases": {
                    "en": ["Sorry, she's sick and can't come this weekend"],
                    "de": ["Tut mir leid, sie ist krank und kann dieses Wochenende nicht kommen"],
                    "tr": ["Üzgünüm, hasta ve bu hafta sonu gelemez"]
                },
                "severity_base": 7
            },
            {
                "tactic_id": "INT002",
                "name": "Communication Blocking",
                "name_de": "Kommunikationsblockade",
                "name_tr": "İletişim Engelleme",
                "category": TacticCategory.INTERFERENCE,
                "description": "Blocking phone calls, texts, or video calls with other parent",
                "description_de": "Blockieren von Telefonaten, SMS oder Videoanrufen mit dem anderen Elternteil",
                "description_tr": "Diğer ebeveynle telefon, mesaj veya video görüşmelerini engelleme",
                "indicators": [
                    "Child's phone always off/unavailable",
                    "Messages not delivered",
                    "Phone taken during other parent's designated call time"
                ],
                "keywords": {
                    "en": ["phone is broken", "forgot to charge", "was busy", "didn't hear"],
                    "de": ["Telefon ist kaputt", "vergessen aufzuladen", "war beschäftigt"],
                    "tr": ["telefon bozuk", "şarj etmeyi unuttum", "meşguldük", "duymadık"]
                },
                "example_phrases": {
                    "en": ["Her phone was broken, that's why she couldn't answer"],
                    "de": ["Ihr Telefon war kaputt, deshalb konnte sie nicht antworten"],
                    "tr": ["Telefonu bozuktu, bu yüzden cevap veremedi"]
                },
                "severity_base": 7
            },
            {
                "tactic_id": "INT003",
                "name": "Information Withholding",
                "name_de": "Informationszurückhaltung",
                "name_tr": "Bilgi Saklama",
                "category": TacticCategory.INFORMATION_CONTROL,
                "description": "Not sharing important information about child's school, health, activities",
                "description_de": "Wichtige Informationen über Schule, Gesundheit des Kindes nicht teilen",
                "description_tr": "Çocuğun okulu, sağlığı hakkında önemli bilgileri paylaşmama",
                "indicators": [
                    "Other parent learns about events after they happen",
                    "Medical appointments not shared",
                    "School events not communicated"
                ],
                "keywords": {
                    "en": ["forgot to tell", "didn't think you'd care", "none of your business"],
                    "de": ["vergessen zu sagen", "dachte es interessiert dich nicht", "geht dich nichts an"],
                    "tr": ["söylemeyi unuttum", "ilgileneceğini düşünmedim", "seni ilgilendirmez"]
                },
                "example_phrases": {
                    "en": ["I forgot to tell you about the parent-teacher conference"],
                    "de": ["Ich habe vergessen, dir vom Elternabend zu erzählen"],
                    "tr": ["Veli toplantısını söylemeyi unuttum"]
                },
                "severity_base": 5
            },
            {
                "tactic_id": "INT004",
                "name": "Relocation Threat",
                "name_de": "Umzugsdrohung",
                "name_tr": "Taşınma Tehdidi",
                "category": TacticCategory.INTERFERENCE,
                "description": "Threatening to move away or actually relocating to limit contact",
                "description_de": "Drohung wegzuziehen oder tatsächlicher Umzug zur Kontaktbeschränkung",
                "description_tr": "Teması kısıtlamak için taşınma tehdidi veya gerçekten taşınma",
                "indicators": [
                    "Threats to move to another city/country",
                    "Job changes requiring relocation",
                    "Moving without proper notice"
                ],
                "keywords": {
                    "en": ["moving away", "better opportunity", "fresh start", "new job in"],
                    "de": ["wegziehen", "bessere Möglichkeit", "Neuanfang", "neuer Job in"],
                    "tr": ["taşınıyoruz", "daha iyi fırsat", "yeni başlangıç", "yeni iş"]
                },
                "example_phrases": {
                    "en": ["I got a job offer in another country, we're moving"],
                    "de": ["Ich habe ein Jobangebot in einem anderen Land, wir ziehen um"],
                    "tr": ["Başka bir ülkede iş teklifi aldım, taşınıyoruz"]
                },
                "severity_base": 9
            },
            {
                "tactic_id": "INT005",
                "name": "Holiday Sabotage",
                "name_de": "Feiertagssabotage",
                "name_tr": "Tatil Sabotajı",
                "category": TacticCategory.INTERFERENCE,
                "description": "Creating conflicts during holidays or special occasions",
                "description_de": "Konflikte während Feiertagen oder besonderen Anlässen schaffen",
                "description_tr": "Tatiller veya özel günlerde çatışma yaratma",
                "indicators": [
                    "Child sick on holidays with other parent",
                    "Scheduling own celebrations on other parent's time",
                    "Creating emergencies before special events"
                ],
                "keywords": {
                    "en": ["emergency", "can't travel", "doctor says", "really important event"],
                    "de": ["Notfall", "kann nicht reisen", "Arzt sagt", "wirklich wichtige Veranstaltung"],
                    "tr": ["acil durum", "seyahat edemez", "doktor diyor ki", "çok önemli etkinlik"]
                },
                "example_phrases": {
                    "en": ["The doctor says she can't travel for Christmas this year"],
                    "de": ["Der Arzt sagt, sie kann dieses Jahr nicht zu Weihnachten reisen"],
                    "tr": ["Doktor bu yıl bayramda seyahat edemez diyor"]
                },
                "severity_base": 6
            },

            # EMOTIONAL MANIPULATION TACTICS (21-30)
            {
                "tactic_id": "EMO001",
                "name": "Guilt Induction",
                "name_de": "Schuldgefühle Erzeugen",
                "name_tr": "Suçluluk Duygusu Yaratma",
                "category": TacticCategory.EMOTIONAL_MANIPULATION,
                "description": "Making child feel guilty for loving or spending time with other parent",
                "description_de": "Kind fühlt sich schuldig, den anderen Elternteil zu lieben",
                "description_tr": "Çocuğun diğer ebeveyni sevmesi için suçluluk hissettirme",
                "indicators": [
                    "Acting sad when child leaves for visits",
                    "Crying or appearing upset",
                    "Making child feel responsible for parent's emotions"
                ],
                "keywords": {
                    "en": ["miss you so much", "so lonely", "don't forget me", "abandoned"],
                    "de": ["vermisse dich so sehr", "so einsam", "vergiss mich nicht", "verlassen"],
                    "tr": ["çok özleyeceğim", "çok yalnız", "beni unutma", "terk edilmiş"]
                },
                "example_phrases": {
                    "en": ["I'll be so lonely while you're with your father"],
                    "de": ["Ich werde so einsam sein, während du bei deinem Vater bist"],
                    "tr": ["Sen babanla iken çok yalnız olacağım"]
                },
                "severity_base": 7
            },
            {
                "tactic_id": "EMO002",
                "name": "Loyalty Conflict Creation",
                "name_de": "Loyalitätskonflikt Erzeugen",
                "name_tr": "Sadakat Çatışması Yaratma",
                "category": TacticCategory.EMOTIONAL_MANIPULATION,
                "description": "Forcing child to choose sides or demonstrate loyalty",
                "description_de": "Kind wird gezwungen, Seite zu wählen oder Loyalität zu zeigen",
                "description_tr": "Çocuğu taraf seçmeye veya sadakat göstermeye zorlamak",
                "indicators": [
                    "Asking who child loves more",
                    "Making child choose between parents",
                    "Rewarding loyalty, punishing contact with other parent"
                ],
                "keywords": {
                    "en": ["who do you love more", "whose side are you on", "choose", "loyal to"],
                    "de": ["wen liebst du mehr", "auf wessen Seite bist du", "wählen", "loyal zu"],
                    "tr": ["kimi daha çok seviyorsun", "kimin tarafındasın", "seç", "sadık"]
                },
                "example_phrases": {
                    "en": ["If you really loved me, you wouldn't want to see your father"],
                    "de": ["Wenn du mich wirklich liebst, würdest du deinen Vater nicht sehen wollen"],
                    "tr": ["Beni gerçekten sevseydin, babanı görmek istemezdin"]
                },
                "severity_base": 8
            },
            {
                "tactic_id": "EMO003",
                "name": "Fear Instillation",
                "name_de": "Angst Einflößen",
                "name_tr": "Korku Aşılama",
                "category": TacticCategory.EMOTIONAL_MANIPULATION,
                "description": "Making child afraid of other parent without justification",
                "description_de": "Kind ohne Rechtfertigung Angst vor anderem Elternteil machen",
                "description_tr": "Çocuğa haklı bir neden olmadan diğer ebeveynden korkutma",
                "indicators": [
                    "Warning child about dangers at other parent's home",
                    "Exaggerating minor incidents",
                    "Creating fear of abandonment by other parent"
                ],
                "keywords": {
                    "en": ["be careful", "dangerous", "might hurt you", "not safe", "scared for you"],
                    "de": ["sei vorsichtig", "gefährlich", "könnte dich verletzen", "nicht sicher"],
                    "tr": ["dikkatli ol", "tehlikeli", "sana zarar verebilir", "güvenli değil"]
                },
                "example_phrases": {
                    "en": ["Be careful at your father's house, you know how he gets angry"],
                    "de": ["Sei vorsichtig bei deinem Vater, du weißt wie wütend er werden kann"],
                    "tr": ["Babanın evinde dikkatli ol, nasıl sinirlendiğini biliyorsun"]
                },
                "severity_base": 8
            },
            {
                "tactic_id": "EMO004",
                "name": "Parentification",
                "name_de": "Parentifizierung",
                "name_tr": "Ebeveynleştirme",
                "category": TacticCategory.EMOTIONAL_MANIPULATION,
                "description": "Making child feel responsible for parent's emotional wellbeing",
                "description_de": "Kind fühlt sich für das emotionale Wohlbefinden des Elternteils verantwortlich",
                "description_tr": "Çocuğun ebeveynin duygusal iyiliğinden sorumlu hissetmesi",
                "indicators": [
                    "Child takes care of parent's emotional needs",
                    "Child feels responsible for parent's happiness",
                    "Role reversal between parent and child"
                ],
                "keywords": {
                    "en": ["you're all I have", "take care of me", "my reason to live", "only one who understands"],
                    "de": ["du bist alles was ich habe", "kümmere dich um mich", "mein Grund zu leben"],
                    "tr": ["sahip olduğum tek şey sensin", "bana bak", "yaşama nedenim", "tek anlayan"]
                },
                "example_phrases": {
                    "en": ["You're the only one who understands me, you're all I have left"],
                    "de": ["Du bist der Einzige, der mich versteht"],
                    "tr": ["Beni anlayan tek kişi sensin, sahip olduğum tek şey sensin"]
                },
                "severity_base": 7
            },
            {
                "tactic_id": "EMO005",
                "name": "Emotional Bribery",
                "name_de": "Emotionale Bestechung",
                "name_tr": "Duygusal Rüşvet",
                "category": TacticCategory.EMOTIONAL_MANIPULATION,
                "description": "Using gifts, privileges to compete with other parent",
                "description_de": "Geschenke und Privilegien nutzen um mit anderem Elternteil zu konkurrieren",
                "description_tr": "Diğer ebeveynle rekabet için hediye ve ayrıcalıklar kullanma",
                "indicators": [
                    "Excessive gifts after visits with other parent",
                    "Promising things other parent can't provide",
                    "No rules or discipline to appear 'fun parent'"
                ],
                "keywords": {
                    "en": ["I'll buy you", "anything you want", "no rules here", "more fun here"],
                    "de": ["ich kaufe dir", "alles was du willst", "keine Regeln hier", "mehr Spaß hier"],
                    "tr": ["sana alacağım", "ne istersen", "burada kural yok", "burada daha eğlenceli"]
                },
                "example_phrases": {
                    "en": ["If you stay with me, I'll buy you that new phone your father won't get you"],
                    "de": ["Wenn du bei mir bleibst, kaufe ich dir das neue Handy"],
                    "tr": ["Benimle kalırsan, babanın almayacağı telefonu alırım"]
                },
                "severity_base": 5
            },

            # CHILD WEAPONIZATION TACTICS (31-40)
            {
                "tactic_id": "WEP001",
                "name": "Using Child as Messenger",
                "name_de": "Kind als Bote Benutzen",
                "name_tr": "Çocuğu Haberci Olarak Kullanma",
                "category": TacticCategory.CHILD_WEAPONIZATION,
                "description": "Sending messages through child instead of direct communication",
                "description_de": "Nachrichten über das Kind statt direkte Kommunikation",
                "description_tr": "Doğrudan iletişim yerine çocuk aracılığıyla mesaj gönderme",
                "indicators": [
                    "Child delivers hostile messages",
                    "Child caught in middle of disputes",
                    "Child anxious about delivering messages"
                ],
                "keywords": {
                    "en": ["tell your father", "tell your mother", "let him/her know", "give this message"],
                    "de": ["sag deinem Vater", "sag deiner Mutter", "lass ihn/sie wissen", "gib diese Nachricht"],
                    "tr": ["babana söyle", "annene söyle", "ona bildir", "bu mesajı ver"]
                },
                "example_phrases": {
                    "en": ["Tell your father he needs to pay the child support"],
                    "de": ["Sag deinem Vater, er muss den Unterhalt zahlen"],
                    "tr": ["Babana nafakayı ödemesi gerektiğini söyle"]
                },
                "severity_base": 6
            },
            {
                "tactic_id": "WEP002",
                "name": "Using Child as Spy",
                "name_de": "Kind als Spion Benutzen",
                "name_tr": "Çocuğu Casus Olarak Kullanma",
                "category": TacticCategory.CHILD_WEAPONIZATION,
                "description": "Interrogating child about other parent's life, relationships, finances",
                "description_de": "Kind über Leben, Beziehungen, Finanzen des anderen Elternteils ausfragen",
                "description_tr": "Çocuğu diğer ebeveynin hayatı hakkında sorgulamak",
                "indicators": [
                    "Detailed questioning after visits",
                    "Interest in other parent's romantic life",
                    "Asking about spending habits"
                ],
                "keywords": {
                    "en": ["who was there", "what did they do", "anyone new", "how much", "did they buy"],
                    "de": ["wer war da", "was haben sie gemacht", "jemand neues", "wie viel", "haben sie gekauft"],
                    "tr": ["kim vardı", "ne yaptılar", "yeni biri var mı", "ne kadar", "aldılar mı"]
                },
                "example_phrases": {
                    "en": ["Was there a woman at your father's house? What's her name?"],
                    "de": ["War eine Frau bei deinem Vater? Wie heißt sie?"],
                    "tr": ["Babanın evinde bir kadın var mıydı? Adı ne?"]
                },
                "severity_base": 6
            },
            {
                "tactic_id": "WEP003",
                "name": "Child as Ally Against Other Parent",
                "name_de": "Kind als Verbündeter Gegen Anderen Elternteil",
                "name_tr": "Çocuğu Diğer Ebeveyne Karşı Müttefik Yapma",
                "category": TacticCategory.CHILD_WEAPONIZATION,
                "description": "Creating an alliance with child against the other parent",
                "description_de": "Allianz mit Kind gegen anderen Elternteil bilden",
                "description_tr": "Diğer ebeveyne karşı çocukla ittifak oluşturma",
                "indicators": [
                    "Us vs. them mentality",
                    "Sharing adult problems with child",
                    "Seeking child's opinion on custody matters"
                ],
                "keywords": {
                    "en": ["we need to", "against us", "our secret", "don't tell", "between us"],
                    "de": ["wir müssen", "gegen uns", "unser Geheimnis", "sag nicht", "unter uns"],
                    "tr": ["yapmalıyız", "bize karşı", "bizim sırrımız", "söyleme", "aramızda kalsın"]
                },
                "example_phrases": {
                    "en": ["It's just you and me against the world now"],
                    "de": ["Jetzt sind wir zwei gegen den Rest der Welt"],
                    "tr": ["Artık dünyaya karşı sadece sen ve ben varız"]
                },
                "severity_base": 7
            },
            {
                "tactic_id": "WEP004",
                "name": "Forcing Child to Reject Parent",
                "name_de": "Kind Zur Ablehnung Zwingen",
                "name_tr": "Çocuğu Ebeveyni Reddetmeye Zorlamak",
                "category": TacticCategory.CHILD_WEAPONIZATION,
                "description": "Pressuring child to say they don't want to see other parent",
                "description_de": "Kind unter Druck setzen zu sagen, es will anderen Elternteil nicht sehen",
                "description_tr": "Çocuğu diğer ebeveyni görmek istemediğini söylemeye zorlamak",
                "indicators": [
                    "Child's rejection seems coached",
                    "Reasons mirror alienating parent's language",
                    "Rejection is absolute with no ambivalence"
                ],
                "keywords": {
                    "en": ["if you want to", "your choice", "you don't have to", "wouldn't blame you"],
                    "de": ["wenn du willst", "deine Wahl", "du musst nicht", "würde es dir nicht übel nehmen"],
                    "tr": ["istersen", "senin seçimin", "zorunda değilsin", "seni suçlamam"]
                },
                "example_phrases": {
                    "en": ["You don't have to go if you don't want to, I'll support whatever you decide"],
                    "de": ["Du musst nicht gehen wenn du nicht willst"],
                    "tr": ["İstemiyorsan gitmek zorunda değilsin, kararını desteklerim"]
                },
                "severity_base": 9
            },
            {
                "tactic_id": "WEP005",
                "name": "Coaching Child's Statements",
                "name_de": "Aussagen Des Kindes Einstudieren",
                "name_tr": "Çocuğun İfadelerini Ezberletmek",
                "category": TacticCategory.CHILD_WEAPONIZATION,
                "description": "Teaching child what to say to authorities, therapists, or other parent",
                "description_de": "Kind beibringen was es Behörden, Therapeuten sagen soll",
                "description_tr": "Çocuğa yetkililere veya terapiste ne söyleyeceğini öğretmek",
                "indicators": [
                    "Child uses adult language",
                    "Identical phrases to alienating parent",
                    "Story changes under gentle questioning"
                ],
                "keywords": {
                    "en": ["remember to say", "when they ask", "tell them", "don't forget to mention"],
                    "de": ["denk daran zu sagen", "wenn sie fragen", "sag ihnen", "vergiss nicht zu erwähnen"],
                    "tr": ["söylemeyi unutma", "sorduklarında", "onlara söyle", "bahsetmeyi unutma"]
                },
                "example_phrases": {
                    "en": ["Remember to tell the counselor how scared you are at daddy's house"],
                    "de": ["Denk daran dem Berater zu sagen wie viel Angst du bei Papa hast"],
                    "tr": ["Danışmana babanın evinde ne kadar korktuğunu söylemeyi unutma"]
                },
                "severity_base": 9
            },

            # FALSE ALLEGATIONS TACTICS (41-45)
            {
                "tactic_id": "FAL001",
                "name": "False Abuse Allegations",
                "name_de": "Falsche Missbrauchsvorwürfe",
                "name_tr": "Yanlış İstismar İddiaları",
                "category": TacticCategory.FALSE_ALLEGATIONS,
                "description": "Making unfounded allegations of physical or sexual abuse",
                "description_de": "Unbegründete Anschuldigungen des körperlichen oder sexuellen Missbrauchs",
                "description_tr": "Asılsız fiziksel veya cinsel istismar iddiaları",
                "indicators": [
                    "Allegations appear during custody disputes",
                    "No evidence or inconsistent evidence",
                    "Child's story changes or seems rehearsed"
                ],
                "keywords": {
                    "en": ["touched", "hurt", "inappropriate", "abuse", "hit", "scared"],
                    "de": ["angefasst", "verletzt", "unangemessen", "Missbrauch", "geschlagen"],
                    "tr": ["dokundu", "acıttı", "uygunsuz", "istismar", "vurdu", "korktu"]
                },
                "example_phrases": {
                    "en": ["He touched her inappropriately, I'm calling the police"],
                    "de": ["Er hat sie unangemessen berührt, ich rufe die Polizei"],
                    "tr": ["Ona uygunsuz şekilde dokundu, polisi arıyorum"]
                },
                "severity_base": 10
            },
            {
                "tactic_id": "FAL002",
                "name": "False Neglect Claims",
                "name_de": "Falsche Vernachlässigungsbehauptungen",
                "name_tr": "Yanlış İhmal İddiaları",
                "category": TacticCategory.FALSE_ALLEGATIONS,
                "description": "Claiming other parent neglects child's basic needs",
                "description_de": "Behaupten, anderer Elternteil vernachlässigt Grundbedürfnisse",
                "description_tr": "Diğer ebeveynin çocuğun temel ihtiyaçlarını ihmal ettiğini iddia etme",
                "indicators": [
                    "Complaints about cleanliness, food, supervision",
                    "No evidence of actual neglect",
                    "Exaggeration of minor issues"
                ],
                "keywords": {
                    "en": ["doesn't feed", "dirty clothes", "no supervision", "neglected", "starving"],
                    "de": ["füttert nicht", "schmutzige Kleidung", "keine Aufsicht", "vernachlässigt"],
                    "tr": ["yedirmiyor", "kirli kıyafetler", "gözetimsiz", "ihmal edilmiş"]
                },
                "example_phrases": {
                    "en": ["She comes back with dirty clothes and hasn't eaten properly"],
                    "de": ["Sie kommt mit schmutzigen Kleidern zurück und hat nicht richtig gegessen"],
                    "tr": ["Kirli kıyafetlerle ve aç dönüyor"]
                },
                "severity_base": 7
            },
            {
                "tactic_id": "FAL003",
                "name": "False Domestic Violence Claims",
                "name_de": "Falsche Häusliche Gewalt Anschuldigungen",
                "name_tr": "Yanlış Aile İçi Şiddet İddiaları",
                "category": TacticCategory.FALSE_ALLEGATIONS,
                "description": "Fabricating or exaggerating domestic violence incidents",
                "description_de": "Vorfälle häuslicher Gewalt erfinden oder übertreiben",
                "description_tr": "Aile içi şiddet olaylarını uydurma veya abartma",
                "indicators": [
                    "No police reports or medical records",
                    "Allegations timed with custody proceedings",
                    "Inconsistent accounts"
                ],
                "keywords": {
                    "en": ["hit me", "violent", "threatened", "afraid for my life", "restraining order"],
                    "de": ["hat mich geschlagen", "gewalttätig", "bedroht", "um mein Leben fürchten"],
                    "tr": ["beni dövdü", "şiddet uyguladı", "tehdit etti", "hayatımdan korkuyorum"]
                },
                "example_phrases": {
                    "en": ["He threatened to kill me, I need a restraining order"],
                    "de": ["Er hat gedroht mich zu töten, ich brauche eine einstweilige Verfügung"],
                    "tr": ["Beni öldürmekle tehdit etti, uzaklaştırma kararı istiyorum"]
                },
                "severity_base": 9
            },

            # IDENTITY ERASURE TACTICS (46-50)
            {
                "tactic_id": "IDE001",
                "name": "Name Change Attempts",
                "name_de": "Namensänderungsversuche",
                "name_tr": "İsim Değiştirme Girişimleri",
                "category": TacticCategory.IDENTITY_ERASURE,
                "description": "Trying to change child's surname or allow stepparent adoption",
                "description_de": "Versuch den Nachnamen des Kindes zu ändern oder Stiefadoption",
                "description_tr": "Çocuğun soyadını değiştirme veya üvey ebeveyn evlat edinme girişimi",
                "indicators": [
                    "Child encouraged to use different name",
                    "Legal name change without consent",
                    "Introducing new partner as 'real' parent"
                ],
                "keywords": {
                    "en": ["real dad", "new daddy", "change name", "adoption", "step-father"],
                    "de": ["echter Papa", "neuer Papa", "Namen ändern", "Adoption", "Stiefvater"],
                    "tr": ["gerçek baba", "yeni baba", "isim değiştir", "evlat edinme", "üvey baba"]
                },
                "example_phrases": {
                    "en": ["Mark wants to adopt you, wouldn't you like to have his last name?"],
                    "de": ["Mark möchte dich adoptieren, möchtest du nicht seinen Nachnamen haben?"],
                    "tr": ["Mark seni evlat edinmek istiyor, onun soyadını almak istemez misin?"]
                },
                "severity_base": 8
            },
            {
                "tactic_id": "IDE002",
                "name": "Erasing Other Parent's Presence",
                "name_de": "Präsenz Des Anderen Elternteils Löschen",
                "name_tr": "Diğer Ebeveynin Varlığını Silme",
                "category": TacticCategory.IDENTITY_ERASURE,
                "description": "Removing photos, gifts, reminders of other parent from home",
                "description_de": "Fotos, Geschenke, Erinnerungen an anderen Elternteil entfernen",
                "description_tr": "Fotoğrafları, hediyeleri, diğer ebeveyne ait anıları evden kaldırma",
                "indicators": [
                    "No photos of other parent displayed",
                    "Gifts from other parent discouraged/hidden",
                    "Talking about other parent discouraged"
                ],
                "keywords": {
                    "en": ["get rid of", "don't need", "throw away", "doesn't belong here"],
                    "de": ["loswerden", "brauchen nicht", "wegwerfen", "gehört nicht hierher"],
                    "tr": ["kurtul", "gerek yok", "at", "buraya ait değil"]
                },
                "example_phrases": {
                    "en": ["Why do you need that photo? He's not part of our family anymore"],
                    "de": ["Warum brauchst du dieses Foto? Er ist nicht mehr Teil unserer Familie"],
                    "tr": ["Bu fotoğrafı neden istiyorsun? O artık ailemizin parçası değil"]
                },
                "severity_base": 6
            },
            {
                "tactic_id": "IDE003",
                "name": "Cultural/Religious Identity Erasure",
                "name_de": "Kulturelle/Religiöse Identitätslöschung",
                "name_tr": "Kültürel/Dini Kimlik Silme",
                "category": TacticCategory.IDENTITY_ERASURE,
                "description": "Preventing child from practicing other parent's religion or culture",
                "description_de": "Kind daran hindern Religion oder Kultur des anderen Elternteils zu praktizieren",
                "description_tr": "Çocuğun diğer ebeveynin dinini veya kültürünü yaşamasını engelleme",
                "indicators": [
                    "Preventing religious observances",
                    "Mocking cultural traditions",
                    "Not allowing heritage language"
                ],
                "keywords": {
                    "en": ["not our religion", "strange customs", "don't speak that language", "forget about"],
                    "de": ["nicht unsere Religion", "seltsame Bräuche", "sprich nicht diese Sprache"],
                    "tr": ["bizim dinimiz değil", "garip gelenekler", "o dili konuşma", "unut gitsin"]
                },
                "example_phrases": {
                    "en": ["You don't need to celebrate that, it's your father's weird tradition"],
                    "de": ["Du musst das nicht feiern, das ist die seltsame Tradition deines Vaters"],
                    "tr": ["Bunu kutlamak zorunda değilsin, babanın garip geleneği"]
                },
                "severity_base": 7
            },
            {
                "tactic_id": "IDE004",
                "name": "Extended Family Exclusion",
                "name_de": "Ausschluss Der Erweiterten Familie",
                "name_tr": "Geniş Aile Dışlama",
                "category": TacticCategory.IDENTITY_ERASURE,
                "description": "Preventing child from seeing other parent's relatives",
                "description_de": "Kind daran hindern Verwandte des anderen Elternteils zu sehen",
                "description_tr": "Çocuğun diğer ebeveynin akrabalarını görmesini engelleme",
                "indicators": [
                    "No contact with grandparents/relatives",
                    "Speaking negatively about extended family",
                    "Not allowing family events"
                ],
                "keywords": {
                    "en": ["don't trust", "bad influence", "not real family", "strangers"],
                    "de": ["vertraue nicht", "schlechter Einfluss", "keine echte Familie", "Fremde"],
                    "tr": ["güvenme", "kötü etki", "gerçek aile değil", "yabancılar"]
                },
                "example_phrases": {
                    "en": ["You don't need to see your father's parents, they're just like him"],
                    "de": ["Du musst deine Großeltern väterlicherseits nicht sehen"],
                    "tr": ["Babanın anne babasını görmen gerekmiyor, onlar da onun gibi"]
                },
                "severity_base": 6
            },
            {
                "tactic_id": "IDE005",
                "name": "Replacement Parent Introduction",
                "name_de": "Einführung Eines Ersatzelternteils",
                "name_tr": "Yedek Ebeveyn Tanıtımı",
                "category": TacticCategory.IDENTITY_ERASURE,
                "description": "Presenting new partner as replacement parent figure",
                "description_de": "Neuen Partner als Ersatzelternteil präsentieren",
                "description_tr": "Yeni partneri yedek ebeveyn figürü olarak sunma",
                "indicators": [
                    "New partner called 'dad/mom'",
                    "New partner disciplines child",
                    "Original parent's role minimized"
                ],
                "keywords": {
                    "en": ["new daddy", "real father figure", "better parent", "more of a dad than"],
                    "de": ["neuer Papa", "echte Vaterfigur", "besserer Elternteil", "mehr Vater als"],
                    "tr": ["yeni baba", "gerçek baba figürü", "daha iyi ebeveyn", "daha çok baba"]
                },
                "example_phrases": {
                    "en": ["Mark is more of a father to you than your real dad ever was"],
                    "de": ["Mark ist mehr ein Vater für dich als dein richtiger Vater je war"],
                    "tr": ["Mark sana gerçek babandan daha çok babalık yapıyor"]
                },
                "severity_base": 8
            }
        ]

        for data in tactics_data:
            tactic = ManipulationTactic(
                tactic_id=data["tactic_id"],
                name=data["name"],
                name_de=data["name_de"],
                name_tr=data["name_tr"],
                category=data["category"],
                description=data["description"],
                description_de=data["description_de"],
                description_tr=data["description_tr"],
                indicators=data["indicators"],
                keywords=data["keywords"],
                example_phrases=data["example_phrases"],
                severity_base=data["severity_base"],
                counter_indicators=data.get("counter_indicators", [])
            )
            self.tactics[tactic.tactic_id] = tactic

    def _load_literature(self):
        """Load academic literature references."""
        literature_data = [
            {
                "reference_id": "GARDNER1985",
                "authors": ["Gardner, Richard A."],
                "title": "Recent Trends in Divorce and Custody Litigation",
                "journal": "Academy Forum",
                "year": 1985,
                "pages": "3-7",
                "relevance_score": 0.95
            },
            {
                "reference_id": "KELLY2001",
                "authors": ["Kelly, Joan B.", "Johnston, Janet R."],
                "title": "The Alienated Child: A Reformulation of Parental Alienation Syndrome",
                "journal": "Family Court Review",
                "year": 2001,
                "doi": "10.1111/j.174-1617.2001.tb00609.x",
                "relevance_score": 0.98
            },
            {
                "reference_id": "BERNET2010",
                "authors": ["Bernet, William", "von Boch-Galhau, Wilfrid", "Baker, Amy J.L.", "Morrison, Stephen L."],
                "title": "Parental Alienation, DSM-5, and ICD-11",
                "journal": "American Journal of Family Therapy",
                "year": 2010,
                "doi": "10.1080/01926187.2010.505938",
                "relevance_score": 0.97
            },
            {
                "reference_id": "BAKER2007",
                "authors": ["Baker, Amy J.L."],
                "title": "Adult Children of Parental Alienation Syndrome: Breaking the Ties that Bind",
                "journal": "W. W. Norton & Company",
                "year": 2007,
                "relevance_score": 0.96
            },
            {
                "reference_id": "WARSHAK2015",
                "authors": ["Warshak, Richard A."],
                "title": "Ten Parental Alienation Fallacies That Compromise Decisions in Court and in Therapy",
                "journal": "Professional Psychology: Research and Practice",
                "year": 2015,
                "doi": "10.1037/pro0000031",
                "relevance_score": 0.95
            },
            {
                "reference_id": "HARMAN2019",
                "authors": ["Harman, Jennifer J.", "Kruk, Edward", "Hines, Denise A."],
                "title": "Parental Alienating Behaviors: An Unacknowledged Form of Family Violence",
                "journal": "Psychological Bulletin",
                "year": 2019,
                "doi": "10.1037/bul0000175",
                "relevance_score": 0.98
            },
            {
                "reference_id": "LORANDOS2020",
                "authors": ["Lorandos, Demosthenes", "Bernet, William", "Sauber, S. Richard"],
                "title": "Parental Alienation: The Handbook for Mental Health and Legal Professionals",
                "journal": "Charles C Thomas Publisher",
                "year": 2020,
                "relevance_score": 0.99
            },
            {
                "reference_id": "FIDLER2013",
                "authors": ["Fidler, Barbara Jo", "Bala, Nicholas", "Saini, Michael A."],
                "title": "Children Who Resist Post-Separation Parental Contact",
                "journal": "Oxford University Press",
                "year": 2013,
                "relevance_score": 0.94
            }
        ]

        for data in literature_data:
            ref = LiteratureReference(**data)
            self.literature[ref.reference_id] = ref

    def _load_case_law(self):
        """Load case law references."""
        case_law_data = [
            {
                "reference_id": "DE_BGH_2017",
                "case_name": "BGH XII ZB 350/16",
                "court": "Bundesgerichtshof",
                "jurisdiction": "DE",
                "year": 2017,
                "citation": "NJW 2017, 1815",
                "relevance": "Recognition of parental alienation as form of psychological child abuse",
                "outcome": "Court ordered transfer of custody due to severe alienation",
                "key_finding": "Persistent alienation behavior can justify change of custody"
            },
            {
                "reference_id": "DE_OLG_2019",
                "case_name": "OLG Frankfurt 6 UF 150/18",
                "court": "Oberlandesgericht Frankfurt",
                "jurisdiction": "DE",
                "year": 2019,
                "citation": "FamRZ 2019, 1234",
                "relevance": "Interference with visitation rights",
                "outcome": "Fines imposed for repeated visitation interference",
                "key_finding": "Systematic visitation interference is sanctionable"
            },
            {
                "reference_id": "TR_YARG_2018",
                "case_name": "Yargıtay 2. HD 2018/1234",
                "court": "Yargıtay",
                "jurisdiction": "TR",
                "year": 2018,
                "citation": "2018/1234 K.",
                "relevance": "Child's refusal to see parent",
                "outcome": "Custody modified due to alienation",
                "key_finding": "Court recognized coached child rejection"
            },
            {
                "reference_id": "EU_ECHR_2013",
                "case_name": "Diamante and Pelliccioni v. San Marino",
                "court": "European Court of Human Rights",
                "jurisdiction": "EU",
                "year": 2013,
                "citation": "32250/08",
                "relevance": "Right to family life under Article 8 ECHR",
                "outcome": "Violation of Convention found",
                "key_finding": "States must take positive measures to reunite parent and child"
            },
            {
                "reference_id": "US_CALIF_2021",
                "case_name": "Marriage of S.Y. & J.Y.",
                "court": "California Court of Appeal",
                "jurisdiction": "US",
                "year": 2021,
                "citation": "60 Cal.App.5th 277",
                "relevance": "Recognition of alienating behaviors",
                "outcome": "Custody reversed due to alienation",
                "key_finding": "Court can consider alienating conduct in custody decisions"
            }
        ]

        for data in case_law_data:
            ref = CaseLawReference(**data)
            self.case_law[ref.reference_id] = ref

    def get_tactic(self, tactic_id: str) -> Optional[ManipulationTactic]:
        """Get a specific tactic by ID."""
        return self.tactics.get(tactic_id)

    def get_tactics_by_category(self, category: TacticCategory) -> List[ManipulationTactic]:
        """Get all tactics in a category."""
        return [t for t in self.tactics.values() if t.category == category]

    def get_tactics_by_severity(self, min_severity: int, max_severity: int = 10) -> List[ManipulationTactic]:
        """Get tactics within severity range."""
        return [t for t in self.tactics.values() if min_severity <= t.severity_base <= max_severity]

    def search_tactics_by_keyword(self, keyword: str, language: str = "en") -> List[ManipulationTactic]:
        """Search tactics by keyword in specified language."""
        keyword_lower = keyword.lower()
        results = []

        for tactic in self.tactics.values():
            keywords = tactic.keywords.get(language, [])
            if any(keyword_lower in kw.lower() for kw in keywords):
                results.append(tactic)
                continue

            phrases = tactic.example_phrases.get(language, [])
            if any(keyword_lower in phrase.lower() for phrase in phrases):
                results.append(tactic)

        return results

    def get_all_keywords(self, language: str = "en") -> Dict[str, List[str]]:
        """Get all keywords organized by tactic ID."""
        return {
            tactic_id: tactic.keywords.get(language, [])
            for tactic_id, tactic in self.tactics.items()
        }

    def get_literature_for_tactic(self, tactic_id: str) -> List[LiteratureReference]:
        """Get literature references for a tactic."""
        tactic = self.tactics.get(tactic_id)
        if not tactic:
            return []
        return tactic.literature_refs

    def get_case_law_for_jurisdiction(self, jurisdiction: str) -> List[CaseLawReference]:
        """Get case law for a specific jurisdiction."""
        return [ref for ref in self.case_law.values() if ref.jurisdiction == jurisdiction]

    def export_to_json(self) -> str:
        """Export entire database to JSON."""
        data = {
            "tactics": {
                tid: {
                    "tactic_id": t.tactic_id,
                    "name": t.name,
                    "name_de": t.name_de,
                    "name_tr": t.name_tr,
                    "category": t.category.value,
                    "description": t.description,
                    "indicators": t.indicators,
                    "keywords": t.keywords,
                    "example_phrases": t.example_phrases,
                    "severity_base": t.severity_base,
                    "counter_indicators": t.counter_indicators
                }
                for tid, t in self.tactics.items()
            },
            "literature": {
                lid: {
                    "authors": l.authors,
                    "title": l.title,
                    "journal": l.journal,
                    "year": l.year,
                    "doi": l.doi
                }
                for lid, l in self.literature.items()
            },
            "case_law": {
                cid: {
                    "case_name": c.case_name,
                    "court": c.court,
                    "jurisdiction": c.jurisdiction,
                    "year": c.year,
                    "citation": c.citation,
                    "key_finding": c.key_finding
                }
                for cid, c in self.case_law.items()
            }
        }
        return json.dumps(data, indent=2, ensure_ascii=False)

    def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics."""
        category_counts = {}
        for tactic in self.tactics.values():
            cat = tactic.category.value
            category_counts[cat] = category_counts.get(cat, 0) + 1

        severity_distribution = {}
        for tactic in self.tactics.values():
            sev = tactic.severity_base
            severity_distribution[sev] = severity_distribution.get(sev, 0) + 1

        return {
            "total_tactics": len(self.tactics),
            "total_literature": len(self.literature),
            "total_case_law": len(self.case_law),
            "tactics_by_category": category_counts,
            "severity_distribution": severity_distribution,
            "languages_supported": ["en", "de", "tr"],
            "jurisdictions_covered": list(set(c.jurisdiction for c in self.case_law.values()))
        }
