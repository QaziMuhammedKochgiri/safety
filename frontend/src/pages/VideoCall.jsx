import React, { useEffect, useRef, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useLanguage } from '../contexts/LanguageContext';
import { useAuth } from '../contexts/AuthContext';
import { Button } from '../components/ui/button';
import { Video, VideoOff, Mic, MicOff, ArrowLeft } from 'lucide-react';

const VideoCall = () => {
  const { language } = useLanguage();
  const { user } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const jitsiContainerRef = useRef(null);
  const jitsiApiRef = useRef(null);
  const [videoEnabled, setVideoEnabled] = useState(true);
  const [audioEnabled, setAudioEnabled] = useState(true);
  const [roomName, setRoomName] = useState('');

  useEffect(() => {
    // Check if user is authenticated
    if (!user) {
      navigate('/login');
      return;
    }

    // Get room name from URL param or generate one
    const room = searchParams.get('room') || `safechild-${user.clientNumber || 'meeting'}-${Date.now()}`;
    setRoomName(room);

    // Load Jitsi Meet API
    const loadJitsiScript = () => {
      if (window.JitsiMeetExternalAPI) {
        initializeJitsi(room);
        return;
      }

      const script = document.createElement('script');
      script.src = 'https://meet.jit.si/external_api.js';
      script.async = true;
      script.onload = () => initializeJitsi(room);
      document.body.appendChild(script);
    };

    loadJitsiScript();

    return () => {
      if (jitsiApiRef.current) {
        jitsiApiRef.current.dispose();
      }
    };
  }, [user, navigate, searchParams]);

  const initializeJitsi = (room) => {
    if (!jitsiContainerRef.current) return;

    const domain = 'meet.jit.si';
    const options = {
      roomName: room,
      width: '100%',
      height: '100%',
      parentNode: jitsiContainerRef.current,
      configOverwrite: {
        startWithAudioMuted: false,
        startWithVideoMuted: false,
        enableWelcomePage: false,
        prejoinPageEnabled: false,
        disableDeepLinking: true,
      },
      interfaceConfigOverwrite: {
        TOOLBAR_BUTTONS: [
          'microphone',
          'camera',
          'closedcaptions',
          'desktop',
          'fullscreen',
          'fodeviceselection',
          'hangup',
          'profile',
          'chat',
          'recording',
          'sharedvideo',
          'settings',
          'raisehand',
          'videoquality',
          'filmstrip',
          'stats',
          'tileview',
        ],
        SHOW_JITSI_WATERMARK: false,
        SHOW_BRAND_WATERMARK: false,
        SHOW_POWERED_BY: false,
        DEFAULT_REMOTE_DISPLAY_NAME: 'Participant',
      },
      userInfo: {
        displayName: user.firstName || user.email || 'User',
        email: user.email || '',
      },
    };

    const api = new window.JitsiMeetExternalAPI(domain, options);
    jitsiApiRef.current = api;

    // Event listeners
    api.addEventListener('videoConferenceJoined', () => {
      console.log('Conference joined');
    });

    api.addEventListener('videoConferenceLeft', () => {
      console.log('Conference left');
      navigate('/portal');
    });

    api.addEventListener('participantJoined', (event) => {
      console.log('Participant joined:', event);
    });
  };

  const toggleVideo = () => {
    if (jitsiApiRef.current) {
      jitsiApiRef.current.executeCommand('toggleVideo');
      setVideoEnabled(!videoEnabled);
    }
  };

  const toggleAudio = () => {
    if (jitsiApiRef.current) {
      jitsiApiRef.current.executeCommand('toggleAudio');
      setAudioEnabled(!audioEnabled);
    }
  };

  const endCall = () => {
    if (jitsiApiRef.current) {
      jitsiApiRef.current.executeCommand('hangup');
    }
    navigate('/portal');
  };

  return (
    <div className="fixed inset-0 bg-gray-900">
      <div className="absolute top-0 left-0 right-0 z-50 bg-black/50 backdrop-blur-sm">
        <div className="container mx-auto px-4 py-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <Button
                variant="ghost"
                onClick={endCall}
                className="text-white hover:bg-white/10"
              >
                <ArrowLeft className="w-4 h-4 mr-2" />
                {language === 'de' ? 'Beenden' : 'End Call'}
              </Button>
              <div className="text-white">
                <p className="text-sm opacity-75">
                  {language === 'de' ? 'Video-Konsultation' : 'Video Consultation'}
                </p>
                <p className="text-xs opacity-60">Room: {roomName}</p>
              </div>
            </div>

            <div className="flex items-center space-x-2">
              <Button
                variant="ghost"
                size="icon"
                onClick={toggleVideo}
                className={`text-white hover:bg-white/10 ${
                  !videoEnabled ? 'bg-red-500 hover:bg-red-600' : ''
                }`}
              >
                {videoEnabled ? (
                  <Video className="w-5 h-5" />
                ) : (
                  <VideoOff className="w-5 h-5" />
                )}
              </Button>
              <Button
                variant="ghost"
                size="icon"
                onClick={toggleAudio}
                className={`text-white hover:bg-white/10 ${
                  !audioEnabled ? 'bg-red-500 hover:bg-red-600' : ''
                }`}
              >
                {audioEnabled ? (
                  <Mic className="w-5 h-5" />
                ) : (
                  <MicOff className="w-5 h-5" />
                )}
              </Button>
            </div>
          </div>
        </div>
      </div>

      <div ref={jitsiContainerRef} className="w-full h-full" />
    </div>
  );
};

export default VideoCall;
