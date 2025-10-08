class AudioController {
    constructor() {
        this.enabled = localStorage.getItem('audioEnabled') === 'true';
        this.sounds = {};
        this.button = null;
        this.setupToggle();
        this.updateButton();
    }
    
    setupToggle() {

    }
    
    enable() {
        this.sounds.sent = new Audio("https://csci-1100.github.io/class_resources_public/assets/audio/message-sent.mp3");
        this.sounds.received = new Audio("https://csci-1100.github.io/class_resources_public/assets/audio/message-received.mp3");
        

        this.sounds.sent.addEventListener('loadeddata', () => {
            console.log('✅ Audio loaded successfully');
        });


        this.sounds.received.addEventListener('loadeddata', () => {
            console.log('✅ Audio loaded successfully');
        });
    }
    

    disable() {
        this.enabled = false;
        localStorage.setItem('audioEnabled', 'false');
        this.updateButton();
    }
    
    updateButton() {
        this.button.textContent = this.enabled ? '🔊 Notification Audio On' : '🔇 Notification Audio Off';
        this.button.className = this.enabled ? 
            'btn btn-sm btn-success' : 'btn btn-sm btn-outline-secondary';
    }
    
    play(type) {
        if (!this.enabled || !this.sounds[type]) return;
        
        volume = volume || 100;

        try{
            // You're in charge of providing a valid AudioFile that can be reached by your web app
            let soundSource = "https://www.w3schools.com/html/horse.mp3";
            let sound = new Audio(soundSource);

            // Set volume
            sound.volume = volume / 100;

            sound.play();
        }catch(error){
            reject(error);
        }
    }
}

// Explicitly attach to window object
window.audioController = new AudioController();

// Also make it available as a global variable
var audioController = window.audioController;