const canvas = document.getElementById('game-canvas');
const ctx = canvas.getContext('2d');
const scoreElement = document.getElementById('score');
const startScreen = document.getElementById('start-screen');
const gameOverScreen = document.getElementById('game-over-screen');
const startBtn = document.getElementById('start-btn');
const restartBtn = document.getElementById('restart-btn');
const finalScoreElement = document.getElementById('final-score');

canvas.width = window.innerWidth;
canvas.height = window.innerHeight;

let score = 0;
let gameActive = false;
let animationId;

class Player {
    constructor(x, y, radius, color) {
        this.x = x;
        this.y = y;
        this.radius = radius;
        this.color = color;
        this.velocity = { x: 0, y: 0 };
        this.speed = 5;
    }

    draw() {
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2, false);
        ctx.fillStyle = this.color;
        ctx.shadowColor = this.color;
        ctx.shadowBlur = 15;
        ctx.fill();
        ctx.closePath();
    }

    update() {
        this.draw();

        // Boundaries
        if (this.x - this.radius + this.velocity.x > 0 && this.x + this.radius + this.velocity.x < canvas.width) {
            this.x += this.velocity.x;
        }
        if (this.y - this.radius + this.velocity.y > 0 && this.y + this.radius + this.velocity.y < canvas.height) {
            this.y += this.velocity.y;
        }
    }
}

class Projectile {
    constructor(x, y, radius, color, velocity) {
        this.x = x;
        this.y = y;
        this.radius = radius;
        this.color = color;
        this.velocity = velocity;
    }

    draw() {
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2, false);
        ctx.fillStyle = this.color;
        ctx.shadowColor = this.color;
        ctx.shadowBlur = 10;
        ctx.fill();
        ctx.closePath();
    }

    update() {
        this.draw();
        this.x += this.velocity.x;
        this.y += this.velocity.y;
    }
}

class Enemy {
    constructor(x, y, radius, color, velocity) {
        this.x = x;
        this.y = y;
        this.radius = radius;
        this.color = color;
        this.velocity = velocity;
    }

    draw() {
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2, false);
        ctx.fillStyle = this.color;
        ctx.shadowColor = this.color;
        ctx.shadowBlur = 20;
        ctx.fill();
        ctx.closePath();
    }

    update() {
        this.draw();
        this.x += this.velocity.x;
        this.y += this.velocity.y;
    }
}

class Particle {
    constructor(x, y, radius, color, velocity) {
        this.x = x;
        this.y = y;
        this.radius = radius;
        this.color = color;
        this.velocity = velocity;
        this.alpha = 1;
    }

    draw() {
        ctx.save();
        ctx.globalAlpha = this.alpha;
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2, false);
        ctx.fillStyle = this.color;
        ctx.fill();
        ctx.restore();
    }

    update() {
        this.draw();
        this.velocity.x *= 0.99;
        this.velocity.y *= 0.99;
        this.x += this.velocity.x;
        this.y += this.velocity.y;
        this.alpha -= 0.01;
    }
}

const x = canvas.width / 2;
const y = canvas.height / 2;

let player = new Player(x, y, 15, '#00ffff');
let projectiles = [];
let enemies = [];
let particles = [];
let spawnInterval;

function init() {
    player = new Player(canvas.width / 2, canvas.height / 2, 15, '#00ffff');
    projectiles = [];
    enemies = [];
    particles = [];
    score = 0;
    scoreElement.innerHTML = score;
    gameActive = true;
}

function spawnEnemies() {
    spawnInterval = setInterval(() => {
        if (!gameActive) return;

        const radius = Math.random() * (30 - 10) + 10;
        let x, y;

        if (Math.random() < 0.5) {
            x = Math.random() < 0.5 ? 0 - radius : canvas.width + radius;
            y = Math.random() * canvas.height;
        } else {
            x = Math.random() * canvas.width;
            y = Math.random() < 0.5 ? 0 - radius : canvas.height + radius;
        }

        const color = `hsl(${Math.random() * 360}, 100%, 50%)`;
        const angle = Math.atan2(player.y - y, player.x - x);
        const velocity = {
            x: Math.cos(angle) * (1 + score * 0.001), // Increase speed with score
            y: Math.sin(angle) * (1 + score * 0.001)
        };

        enemies.push(new Enemy(x, y, radius, color, velocity));
    }, 1000);
}

function animate() {
    animationId = requestAnimationFrame(animate);
    ctx.fillStyle = 'rgba(5, 5, 16, 0.2)'; // Create trail effect
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    player.update();

    particles.forEach((particle, index) => {
        if (particle.alpha <= 0) {
            particles.splice(index, 1);
        } else {
            particle.update();
        }
    });

    projectiles.forEach((projectile, index) => {
        projectile.update();

        // Remove projectile if off screen
        if (projectile.x + projectile.radius < 0 ||
            projectile.x - projectile.radius > canvas.width ||
            projectile.y + projectile.radius < 0 ||
            projectile.y - projectile.radius > canvas.height) {
            setTimeout(() => {
                projectiles.splice(index, 1);
            }, 0);
        }
    });

    enemies.forEach((enemy, index) => {
        enemy.update();

        // End Game
        const dist = Math.hypot(player.x - enemy.x, player.y - enemy.y);
        if (dist - enemy.radius - player.radius < 1) {
            cancelAnimationFrame(animationId);
            clearInterval(spawnInterval);
            gameActive = false;
            gameOverScreen.classList.add('active');
            finalScoreElement.innerHTML = `Final Score: ${score}`;
        }

        projectiles.forEach((projectile, projectileIndex) => {
            const dist = Math.hypot(projectile.x - enemy.x, projectile.y - enemy.y);

            // Projectile hits enemy
            if (dist - enemy.radius - projectile.radius < 1) {

                // Create explosions
                for (let i = 0; i < enemy.radius * 2; i++) {
                    particles.push(new Particle(
                        projectile.x,
                        projectile.y,
                        Math.random() * 3,
                        enemy.color,
                        {
                            x: (Math.random() - 0.5) * (Math.random() * 6),
                            y: (Math.random() - 0.5) * (Math.random() * 6)
                        }
                    ));
                }

                if (enemy.radius - 10 > 10) {
                    // Shrink enemy
                    score += 10;
                    scoreElement.innerHTML = score;
                    gsap.to(enemy, {
                        radius: enemy.radius - 10
                    });
                    setTimeout(() => {
                        projectiles.splice(projectileIndex, 1);
                    }, 0);
                } else {
                    // Remove enemy
                    score += 25;
                    scoreElement.innerHTML = score;
                    setTimeout(() => {
                        enemies.splice(index, 1);
                        projectiles.splice(projectileIndex, 1);
                    }, 0);
                }
            }
        });
    });
}

// Controls
const keys = {
    w: false,
    a: false,
    s: false,
    d: false,
    ArrowUp: false,
    ArrowLeft: false,
    ArrowDown: false,
    ArrowRight: false
};

window.addEventListener('keydown', (e) => {
    if (keys.hasOwnProperty(e.key)) {
        keys[e.key] = true;
    }
});

window.addEventListener('keyup', (e) => {
    if (keys.hasOwnProperty(e.key)) {
        keys[e.key] = false;
    }
});

function updatePlayerVelocity() {
    if (!gameActive) return;

    player.velocity.x = 0;
    player.velocity.y = 0;

    if (keys.w || keys.ArrowUp) player.velocity.y = -player.speed;
    if (keys.s || keys.ArrowDown) player.velocity.y = player.speed;
    if (keys.a || keys.ArrowLeft) player.velocity.x = -player.speed;
    if (keys.d || keys.ArrowRight) player.velocity.x = player.speed;

    // Normalize diagonal movement
    if (player.velocity.x !== 0 && player.velocity.y !== 0) {
        player.velocity.x *= Math.SQRT1_2;
        player.velocity.y *= Math.SQRT1_2;
    }
}

// Run updatePlayerVelocity in a loop independent of requestAnimationFrame for smoother input handling
setInterval(updatePlayerVelocity, 1000 / 60);

// Shooting
window.addEventListener('click', (e) => {
    if (!gameActive) return;

    const angle = Math.atan2(e.clientY - player.y, e.clientX - player.x);
    const velocity = {
        x: Math.cos(angle) * 10,
        y: Math.sin(angle) * 10
    };

    projectiles.push(new Projectile(player.x, player.y, 5, '#ffff00', velocity));
});

window.addEventListener('keydown', (e) => {
    if (e.code === 'Space' && gameActive) {
        // Shoot right by default if using spacebar without mouse
        const velocity = { x: 10, y: 0 };
        projectiles.push(new Projectile(player.x, player.y, 5, '#ffff00', velocity));
    }
});


// Resize canvas on window resize
window.addEventListener('resize', () => {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
    if (!gameActive) {
        // Redraw initial state if game hasn't started
        ctx.fillStyle = '#050510';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        player.x = canvas.width / 2;
        player.y = canvas.height / 2;
        player.draw();
    }
});

startBtn.addEventListener('click', () => {
    init();
    animate();
    spawnEnemies();
    startScreen.classList.remove('active');
});

restartBtn.addEventListener('click', () => {
    init();
    animate();
    spawnEnemies();
    gameOverScreen.classList.remove('active');
});

// Initial draw
ctx.fillStyle = '#050510';
ctx.fillRect(0, 0, canvas.width, canvas.height);
player.draw();