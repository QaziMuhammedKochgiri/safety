"""
App Shell Manager
Manages the PWA app shell, navigation, and state persistence.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum
import datetime
import hashlib


class ScreenOrientation(str, Enum):
    """Screen orientation modes."""
    PORTRAIT = "portrait"
    LANDSCAPE = "landscape"
    PORTRAIT_PRIMARY = "portrait-primary"
    PORTRAIT_SECONDARY = "portrait-secondary"
    LANDSCAPE_PRIMARY = "landscape-primary"
    LANDSCAPE_SECONDARY = "landscape-secondary"
    ANY = "any"
    NATURAL = "natural"


class DisplayMode(str, Enum):
    """PWA display modes."""
    BROWSER = "browser"
    STANDALONE = "standalone"
    FULLSCREEN = "fullscreen"
    MINIMAL_UI = "minimal-ui"


class ThemeMode(str, Enum):
    """UI theme modes."""
    LIGHT = "light"
    DARK = "dark"
    AUTO = "auto"  # Follow system


class NavigationType(str, Enum):
    """Types of navigation."""
    PUSH = "push"  # Normal navigation
    REPLACE = "replace"  # Replace current entry
    BACK = "back"
    FORWARD = "forward"
    RELOAD = "reload"
    DEEP_LINK = "deep_link"


@dataclass
class ShellConfig:
    """PWA shell configuration."""
    app_name: str
    short_name: str
    description: str
    version: str
    build_number: int

    # Display
    display_mode: DisplayMode
    orientation: ScreenOrientation
    theme_color: str
    background_color: str

    # Icons
    icons: Dict[str, str]  # size -> path

    # Start URL
    start_url: str
    scope: str

    # Features
    supports_offline: bool
    supports_push: bool
    supports_share_target: bool
    supports_file_handling: bool

    # Shortcuts
    shortcuts: List[Dict[str, str]]

    # Screenshots
    screenshots: List[Dict[str, str]]


@dataclass
class NavigationEntry:
    """A navigation history entry."""
    entry_id: str
    url: str
    title: str
    timestamp: str
    navigation_type: NavigationType
    scroll_position: int
    state: Optional[Dict[str, Any]]
    can_go_back: bool
    can_go_forward: bool


@dataclass
class NavigationHistory:
    """Navigation history for a session."""
    session_id: str
    entries: List[NavigationEntry]
    current_index: int
    max_entries: int = 50

    def current_entry(self) -> Optional[NavigationEntry]:
        if 0 <= self.current_index < len(self.entries):
            return self.entries[self.current_index]
        return None

    def can_go_back(self) -> bool:
        return self.current_index > 0

    def can_go_forward(self) -> bool:
        return self.current_index < len(self.entries) - 1


@dataclass
class AppState:
    """Persistent application state."""
    state_id: str
    user_id: str
    device_id: str

    # Navigation
    last_url: str
    navigation_history: NavigationHistory

    # UI state
    theme_mode: ThemeMode
    font_size: str  # small, medium, large
    reduced_motion: bool
    high_contrast: bool
    language: str

    # Feature states
    sidebar_collapsed: bool
    active_case_id: Optional[str]
    active_tab: Optional[str]

    # Form drafts (auto-saved)
    form_drafts: Dict[str, Dict[str, Any]]

    # Timestamps
    created_at: str
    updated_at: str
    last_active: str


@dataclass
class InstallPrompt:
    """PWA install prompt configuration."""
    prompt_id: str
    user_id: str
    device_id: str
    shown_at: str
    user_response: Optional[str]  # accepted, dismissed, later
    responded_at: Optional[str]
    times_shown: int
    next_prompt_date: Optional[str]


class AppShellManager:
    """Manages the PWA app shell and navigation."""

    # Default shell configuration
    DEFAULT_CONFIG = ShellConfig(
        app_name="SafeChild",
        short_name="SafeChild",
        description="Digital forensics platform for family law protection",
        version="2.0.0",
        build_number=20260401,
        display_mode=DisplayMode.STANDALONE,
        orientation=ScreenOrientation.ANY,
        theme_color="#2563eb",  # Blue
        background_color="#ffffff",
        icons={
            "72": "/icons/icon-72x72.png",
            "96": "/icons/icon-96x96.png",
            "128": "/icons/icon-128x128.png",
            "144": "/icons/icon-144x144.png",
            "152": "/icons/icon-152x152.png",
            "192": "/icons/icon-192x192.png",
            "384": "/icons/icon-384x384.png",
            "512": "/icons/icon-512x512.png"
        },
        start_url="/",
        scope="/",
        supports_offline=True,
        supports_push=True,
        supports_share_target=True,
        supports_file_handling=True,
        shortcuts=[
            {
                "name": "Dashboard",
                "short_name": "Dashboard",
                "description": "Go to dashboard",
                "url": "/dashboard",
                "icons": [{"src": "/icons/dashboard.png", "sizes": "96x96"}]
            },
            {
                "name": "Add Evidence",
                "short_name": "Evidence",
                "description": "Capture new evidence",
                "url": "/evidence/new",
                "icons": [{"src": "/icons/evidence.png", "sizes": "96x96"}]
            },
            {
                "name": "Emergency",
                "short_name": "Emergency",
                "description": "Emergency contacts and actions",
                "url": "/emergency",
                "icons": [{"src": "/icons/emergency.png", "sizes": "96x96"}]
            }
        ],
        screenshots=[
            {
                "src": "/screenshots/dashboard.png",
                "sizes": "1280x720",
                "type": "image/png",
                "label": "Dashboard view"
            },
            {
                "src": "/screenshots/evidence.png",
                "sizes": "1280x720",
                "type": "image/png",
                "label": "Evidence capture"
            }
        ]
    )

    # Protected routes requiring authentication
    PROTECTED_ROUTES = [
        "/dashboard",
        "/evidence",
        "/cases",
        "/experts",
        "/profile",
        "/settings"
    ]

    # Routes available offline
    OFFLINE_ROUTES = [
        "/",
        "/offline",
        "/login",
        "/dashboard",
        "/evidence",
        "/emergency"
    ]

    def __init__(self, config: Optional[ShellConfig] = None):
        self.config = config or self.DEFAULT_CONFIG
        self.app_states: Dict[str, AppState] = {}
        self.navigation_histories: Dict[str, NavigationHistory] = {}
        self.install_prompts: Dict[str, InstallPrompt] = {}

    def get_manifest(self) -> Dict[str, Any]:
        """Generate the web app manifest."""
        manifest = {
            "name": self.config.app_name,
            "short_name": self.config.short_name,
            "description": self.config.description,
            "start_url": self.config.start_url,
            "scope": self.config.scope,
            "display": self.config.display_mode.value,
            "orientation": self.config.orientation.value,
            "theme_color": self.config.theme_color,
            "background_color": self.config.background_color,
            "icons": [
                {
                    "src": path,
                    "sizes": f"{size}x{size}",
                    "type": "image/png",
                    "purpose": "any maskable"
                }
                for size, path in self.config.icons.items()
            ],
            "shortcuts": self.config.shortcuts,
            "screenshots": self.config.screenshots
        }

        # Add share target if supported
        if self.config.supports_share_target:
            manifest["share_target"] = {
                "action": "/share",
                "method": "POST",
                "enctype": "multipart/form-data",
                "params": {
                    "title": "title",
                    "text": "text",
                    "url": "url",
                    "files": [
                        {
                            "name": "media",
                            "accept": ["image/*", "video/*", "audio/*"]
                        }
                    ]
                }
            }

        # Add file handlers if supported
        if self.config.supports_file_handling:
            manifest["file_handlers"] = [
                {
                    "action": "/open-file",
                    "accept": {
                        "image/*": [".jpg", ".jpeg", ".png", ".gif", ".webp"],
                        "video/*": [".mp4", ".webm", ".mov"],
                        "audio/*": [".mp3", ".wav", ".ogg", ".m4a"],
                        "application/pdf": [".pdf"]
                    }
                }
            ]

        return manifest

    def create_app_state(
        self,
        user_id: str,
        device_id: str,
        language: str = "en",
        theme_mode: ThemeMode = ThemeMode.AUTO
    ) -> AppState:
        """Create initial app state for a user/device."""
        state_id = hashlib.md5(
            f"{user_id}-{device_id}".encode()
        ).hexdigest()[:12]

        # Create navigation history
        history = NavigationHistory(
            session_id=state_id,
            entries=[],
            current_index=-1
        )
        self.navigation_histories[state_id] = history

        now = datetime.datetime.now().isoformat()

        state = AppState(
            state_id=state_id,
            user_id=user_id,
            device_id=device_id,
            last_url="/",
            navigation_history=history,
            theme_mode=theme_mode,
            font_size="medium",
            reduced_motion=False,
            high_contrast=False,
            language=language,
            sidebar_collapsed=False,
            active_case_id=None,
            active_tab=None,
            form_drafts={},
            created_at=now,
            updated_at=now,
            last_active=now
        )

        self.app_states[state_id] = state
        return state

    def get_or_create_state(
        self,
        user_id: str,
        device_id: str
    ) -> AppState:
        """Get existing state or create new one."""
        state_id = hashlib.md5(
            f"{user_id}-{device_id}".encode()
        ).hexdigest()[:12]

        if state_id in self.app_states:
            state = self.app_states[state_id]
            state.last_active = datetime.datetime.now().isoformat()
            return state

        return self.create_app_state(user_id, device_id)

    def navigate(
        self,
        state_id: str,
        url: str,
        title: str,
        navigation_type: NavigationType = NavigationType.PUSH,
        state: Optional[Dict[str, Any]] = None
    ) -> Optional[NavigationEntry]:
        """Record a navigation event."""
        if state_id not in self.app_states:
            return None

        app_state = self.app_states[state_id]
        history = app_state.navigation_history

        entry_id = hashlib.md5(
            f"{state_id}-{url}-{datetime.datetime.now().isoformat()}".encode()
        ).hexdigest()[:10]

        entry = NavigationEntry(
            entry_id=entry_id,
            url=url,
            title=title,
            timestamp=datetime.datetime.now().isoformat(),
            navigation_type=navigation_type,
            scroll_position=0,
            state=state,
            can_go_back=True,
            can_go_forward=False
        )

        if navigation_type == NavigationType.PUSH:
            # Remove forward history if any
            if history.current_index < len(history.entries) - 1:
                history.entries = history.entries[:history.current_index + 1]

            # Add new entry
            history.entries.append(entry)
            history.current_index = len(history.entries) - 1

            # Trim history if too long
            if len(history.entries) > history.max_entries:
                history.entries = history.entries[-history.max_entries:]
                history.current_index = len(history.entries) - 1

        elif navigation_type == NavigationType.REPLACE:
            if history.entries:
                history.entries[history.current_index] = entry
            else:
                history.entries.append(entry)
                history.current_index = 0

        elif navigation_type == NavigationType.BACK:
            if history.can_go_back():
                history.current_index -= 1
                entry = history.entries[history.current_index]

        elif navigation_type == NavigationType.FORWARD:
            if history.can_go_forward():
                history.current_index += 1
                entry = history.entries[history.current_index]

        # Update app state
        app_state.last_url = url
        app_state.updated_at = datetime.datetime.now().isoformat()

        return entry

    def save_scroll_position(
        self,
        state_id: str,
        scroll_position: int
    ) -> bool:
        """Save scroll position for current page."""
        if state_id not in self.app_states:
            return False

        history = self.app_states[state_id].navigation_history
        current = history.current_entry()
        if current:
            current.scroll_position = scroll_position
            return True
        return False

    def save_form_draft(
        self,
        state_id: str,
        form_id: str,
        form_data: Dict[str, Any]
    ) -> bool:
        """Save a form draft for auto-recovery."""
        if state_id not in self.app_states:
            return False

        self.app_states[state_id].form_drafts[form_id] = {
            "data": form_data,
            "saved_at": datetime.datetime.now().isoformat()
        }
        return True

    def get_form_draft(
        self,
        state_id: str,
        form_id: str
    ) -> Optional[Dict[str, Any]]:
        """Retrieve a saved form draft."""
        if state_id not in self.app_states:
            return None

        draft = self.app_states[state_id].form_drafts.get(form_id)
        return draft.get("data") if draft else None

    def clear_form_draft(
        self,
        state_id: str,
        form_id: str
    ) -> bool:
        """Clear a form draft after successful submission."""
        if state_id not in self.app_states:
            return False

        if form_id in self.app_states[state_id].form_drafts:
            del self.app_states[state_id].form_drafts[form_id]
            return True
        return False

    def update_ui_settings(
        self,
        state_id: str,
        theme_mode: Optional[ThemeMode] = None,
        font_size: Optional[str] = None,
        reduced_motion: Optional[bool] = None,
        high_contrast: Optional[bool] = None,
        language: Optional[str] = None,
        sidebar_collapsed: Optional[bool] = None
    ) -> bool:
        """Update UI settings."""
        if state_id not in self.app_states:
            return False

        state = self.app_states[state_id]

        if theme_mode is not None:
            state.theme_mode = theme_mode
        if font_size is not None:
            state.font_size = font_size
        if reduced_motion is not None:
            state.reduced_motion = reduced_motion
        if high_contrast is not None:
            state.high_contrast = high_contrast
        if language is not None:
            state.language = language
        if sidebar_collapsed is not None:
            state.sidebar_collapsed = sidebar_collapsed

        state.updated_at = datetime.datetime.now().isoformat()
        return True

    def set_active_case(
        self,
        state_id: str,
        case_id: Optional[str]
    ) -> bool:
        """Set the active case context."""
        if state_id not in self.app_states:
            return False

        self.app_states[state_id].active_case_id = case_id
        self.app_states[state_id].updated_at = datetime.datetime.now().isoformat()
        return True

    def is_route_protected(self, url: str) -> bool:
        """Check if a route requires authentication."""
        for protected in self.PROTECTED_ROUTES:
            if url.startswith(protected):
                return True
        return False

    def is_route_offline_available(self, url: str) -> bool:
        """Check if a route is available offline."""
        for offline in self.OFFLINE_ROUTES:
            if url.startswith(offline):
                return True
        return False

    def record_install_prompt(
        self,
        user_id: str,
        device_id: str
    ) -> InstallPrompt:
        """Record that install prompt was shown."""
        prompt_id = hashlib.md5(
            f"install-{user_id}-{device_id}".encode()
        ).hexdigest()[:10]

        existing = self.install_prompts.get(prompt_id)
        now = datetime.datetime.now()

        if existing:
            existing.times_shown += 1
            existing.shown_at = now.isoformat()
            return existing

        prompt = InstallPrompt(
            prompt_id=prompt_id,
            user_id=user_id,
            device_id=device_id,
            shown_at=now.isoformat(),
            user_response=None,
            responded_at=None,
            times_shown=1,
            next_prompt_date=None
        )

        self.install_prompts[prompt_id] = prompt
        return prompt

    def record_install_response(
        self,
        prompt_id: str,
        response: str  # accepted, dismissed, later
    ) -> bool:
        """Record user response to install prompt."""
        if prompt_id not in self.install_prompts:
            return False

        prompt = self.install_prompts[prompt_id]
        prompt.user_response = response
        prompt.responded_at = datetime.datetime.now().isoformat()

        # Schedule next prompt if deferred
        if response == "later":
            next_date = datetime.datetime.now() + datetime.timedelta(days=7)
            prompt.next_prompt_date = next_date.isoformat()
        elif response == "dismissed":
            # Don't show for a month
            next_date = datetime.datetime.now() + datetime.timedelta(days=30)
            prompt.next_prompt_date = next_date.isoformat()

        return True

    def should_show_install_prompt(
        self,
        user_id: str,
        device_id: str
    ) -> bool:
        """Determine if install prompt should be shown."""
        prompt_id = hashlib.md5(
            f"install-{user_id}-{device_id}".encode()
        ).hexdigest()[:10]

        prompt = self.install_prompts.get(prompt_id)

        if not prompt:
            return True  # First time

        if prompt.user_response == "accepted":
            return False  # Already installed

        if prompt.next_prompt_date:
            next_date = datetime.datetime.fromisoformat(prompt.next_prompt_date)
            if datetime.datetime.now() < next_date:
                return False  # Not yet time

        # Show if less than 3 times shown
        return prompt.times_shown < 3

    def export_state(self, state_id: str) -> Optional[Dict[str, Any]]:
        """Export app state for backup/transfer."""
        if state_id not in self.app_states:
            return None

        state = self.app_states[state_id]
        history = state.navigation_history

        return {
            "state_id": state.state_id,
            "user_id": state.user_id,
            "device_id": state.device_id,
            "last_url": state.last_url,
            "theme_mode": state.theme_mode.value,
            "font_size": state.font_size,
            "reduced_motion": state.reduced_motion,
            "high_contrast": state.high_contrast,
            "language": state.language,
            "sidebar_collapsed": state.sidebar_collapsed,
            "active_case_id": state.active_case_id,
            "form_drafts": state.form_drafts,
            "navigation": {
                "current_index": history.current_index,
                "entries": [
                    {
                        "url": e.url,
                        "title": e.title,
                        "timestamp": e.timestamp,
                        "scroll_position": e.scroll_position
                    }
                    for e in history.entries[-10:]  # Last 10 entries
                ]
            },
            "exported_at": datetime.datetime.now().isoformat()
        }

    def import_state(
        self,
        state_data: Dict[str, Any],
        user_id: str,
        device_id: str
    ) -> AppState:
        """Import app state from backup."""
        state = self.create_app_state(user_id, device_id)

        # Restore settings
        if "theme_mode" in state_data:
            state.theme_mode = ThemeMode(state_data["theme_mode"])
        if "font_size" in state_data:
            state.font_size = state_data["font_size"]
        if "reduced_motion" in state_data:
            state.reduced_motion = state_data["reduced_motion"]
        if "high_contrast" in state_data:
            state.high_contrast = state_data["high_contrast"]
        if "language" in state_data:
            state.language = state_data["language"]
        if "sidebar_collapsed" in state_data:
            state.sidebar_collapsed = state_data["sidebar_collapsed"]
        if "form_drafts" in state_data:
            state.form_drafts = state_data["form_drafts"]

        return state

    def get_statistics(self) -> Dict[str, Any]:
        """Get app shell statistics."""
        total_states = len(self.app_states)
        total_prompts = len(self.install_prompts)
        installs = sum(
            1 for p in self.install_prompts.values()
            if p.user_response == "accepted"
        )

        # Theme distribution
        themes = {}
        for state in self.app_states.values():
            theme = state.theme_mode.value
            themes[theme] = themes.get(theme, 0) + 1

        # Language distribution
        languages = {}
        for state in self.app_states.values():
            lang = state.language
            languages[lang] = languages.get(lang, 0) + 1

        return {
            "total_app_states": total_states,
            "total_install_prompts": total_prompts,
            "successful_installs": installs,
            "install_rate": round(installs / total_prompts * 100, 2) if total_prompts > 0 else 0,
            "themes": themes,
            "languages": languages
        }
