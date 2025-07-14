export const environment = {
  production: true,
  apiUrl: 'http://greekstt-research.gr/api',
  wsUrl: 'ws://greekstt-research.gr/ws',
  supportedFormats: {
    audio: ['.mp3', '.wav', '.m4a', '.ogg', '.webm', '.flac', '.opus', '.wma', '.aac'],
    video: ['.mp4', '.avi', '.mov', '.mkv', '.webm']
  },
  maxFileSize: 1073741824, // 1GB for audio files
  maxVideoFileSize: 10737418240, // 10GB for video files
  theme: {
    default: 'dark',
    enableSystemPreference: true,
    animationDuration: 300
  },
  features: {
    audioTranscription: true,
    videoTranscription: true,
    realTimeTranscription: false,
    themeToggle: true
  }
};