class MessageQueue {
    constructor(element, duration, options) {
        // Create an empty queue
        this.messages = [];

        // Set status to waiting for new messages
        this.status = 'waiting';

        // Duration of text being visible, in miliseconds.
        // Default is 2 seconds
        this.duration = duration || 2000;

        // Message element selector
        this.msgElementSelector = element;

        // Gets start animation from options, or default
        this.startAnimation = options.startAnimation || 'fadeIn';

        // Gets end animation from options, or default
        this.endAnimation = options.endAnimation || 'fadeOut';

        //Get avatar
        this.avatar = document.querySelector(options.avatar);
        console.log(this.avatar);
        // If the animated element is different from the element
        // where the message if being shown. Otherwise, the element itself.
        // For example: A parent element.
        this.animatedElementSelector = options.animatedElement || element;

        // Query the Node Element
        this._msgElement = document.querySelector(this.msgElementSelector);

        // Query the Animated Node Element
        this._animatedElement = document.querySelector(this.animatedElementSelector);

        // Check if the element is animated
        if (!this._animatedElement.classList.contains("animated")) {
            this._animatedElement.classList.add("animated");
        }

        // Listen for when animations end, to process the next message in the list
        this._animatedElement.addEventListener('animationend', (event) => {
            const target = event.target;

            if (target.classList.contains(this.startAnimation)) {
                target.classList.remove(this.startAnimation);

                setTimeout(() => {
                    target.classList.add(this.endAnimation);
                }, this.duration);
            } else {
                target.classList.add("msgInvisible");
                target.classList.remove(this.endAnimation);

                this._processNext();
            }
        });
    }

    addMessages(msg) {
        if (typeof msg == "string") {
            this.messages.push(msg);
        }

        if (Array.isArray(msg)) {
            this.messages = this.messages.concat(msg);
        }


        if (this._isWaiting()) {
            this._processNext();
        }

    }

    _isWaiting() {
        return this.status === 'waiting';
    }

    _processNext() {
        // Set status as actively processing messages in the queue
        this.status = 'active';

        if (this.messages.length > 0) {
            const currentMsg = this.messages.shift();
            this.avatar.src = currentMsg.split(';')[0];
            this._msgElement.textContent = currentMsg.split(';')[1];
            this._animatedElement.classList.add(this.startAnimation);

            if (this._animatedElement.classList.contains("msgInvisible")) {
                this._animatedElement.classList.remove("msgInvisible");
            }
        } else {
            // Queue is now empty and waiting for new messages
            this.status = 'waiting';
            this._msgElement.textContent = "";
        }
    }
}