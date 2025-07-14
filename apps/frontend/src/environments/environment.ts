export const environment = {
  production: false,
  apiUrl: 'http://localhost:5001/api',
  wsUrl: 'http://localhost:5001',
  supportedFormats: {
    audio: ['.mp3', '.wav', '.m4a', '.ogg', '.webm', '.flac', '.opus', '.wma', '.aac'],
    video: ['.mp4', '.avi', '.mov', '.mkv', '.webm']
  },
  maxFileSize: 1073741824, // 1GB for audio files
  maxVideoFileSize: 10737418240, // 10GB for video files
  theme: {
    default: 'dark', // Default to dark mode
    enableSystemPreference: true,
    animationDuration: 300 // Theme transition duration in ms
  },
  features: {
    audioTranscription: true,
    videoTranscription: true,
    realTimeTranscription: false,
    themeToggle: true
  }
};