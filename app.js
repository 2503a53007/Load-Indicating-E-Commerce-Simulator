
const $ = id => document.getElementById(id);

const state = {
    running: false,
    elapsed: 0,
    totalRequests: 0,
    timer: null,
    sampleTimer: null,
    level: "MEDIUM",
    samples: Array(30).fill(0).map(() => 35 + Math.random() * 25)
};

const loadConfig = {
    LOW: {
        requests: 18,
        cpu: 22,
        network: 1.8,
        angle: 0,
        description: "Low traffic — system operating normally.",
        color: "#20b879"
    },
    MEDIUM: {
        requests: 44,
        cpu: 38,
        network: 3.4,
        angle: 90,
        description: "Moderate incoming requests detected.",
        color: "#e7ae3e"
    },
    HIGH: {
        requests: 86,
        cpu: 82,
        network: 7.6,
        angle: 180,
        description: "High traffic — additional capacity may be required.",
        color: "#e45c62"
    }
};

function setLevel(level) {
    const config = loadConfig[level];
    state.level = level;

    $("trafficLevel").textContent = level;
    $("trafficBadge").textContent = level;
    $("trafficBadge").className = `badge ${level.toLowerCase()}`;

    $("trafficDescription").textContent = config.description;
    $("requests").textContent = config.requests;
    $("cpu").innerHTML = `${config.cpu}<span>%</span>`;
    $("network").innerHTML = `${config.network} <span>MB/s</span>`;

    $("servoAngle").textContent = `${config.angle}°`;
    $("servoState").textContent = `${level} LOAD`;

    $("alertBanner").style.borderColor =
        level === "LOW" ? "#b9e9d2" :
        level === "MEDIUM" ? "#f0dcae" : "#f2c5c5";

    $("alertBanner").style.background =
        level === "LOW" ? "#ecfaf2" :
        level === "MEDIUM" ? "#fff8e8" : "#fff0f0";

    $("alertBanner").style.color = config.color;

    $("alertBanner").innerHTML =
        `<strong>${level} TRAFFIC · ${level === "HIGH" ? "ATTENTION" : level === "MEDIUM" ? "MONITOR" : "NORMAL"}</strong>
        <p>${config.description}</p>`;
}

function updateActivity(message) {
    $("activityText").textContent = message;
    $("activityTime").textContent =
        new Date().toLocaleTimeString();
}

function showToast(message) {
    const toast = $("toast");
    toast.textContent = message;
    toast.classList.add("show");

    setTimeout(() => {
        toast.classList.remove("show");
    }, 2200);
}

function updateRunStatus(message) {
    $("runStatus").textContent = message;
}

function updateTimer() {
    const remaining = Math.max(0, 300 - state.elapsed);
    const minutes = Math.floor(remaining / 60);
    const seconds = remaining % 60;

    $("startBtn").textContent =
        state.running
            ? `▶ Running ${minutes}:${String(seconds).padStart(2, "0")}`
            : "▶ Start 5-Minute Live Demo";
}

function addSample() {
    const config = loadConfig[state.level];

    const variation = (Math.random() - 0.5) * 12;
    const value = Math.max(0, Math.min(100, config.cpu + variation));

    state.samples.push(value);
    state.samples.shift();

    state.totalRequests += config.requests * 2;

    $("totalRequests").textContent =
        state.totalRequests.toLocaleString("en-IN");

    drawChart();
}

function drawChart() {
    const canvas = $("trafficChart");
    const rect = canvas.getBoundingClientRect();

    if (!rect.width || !rect.height) return;

    const dpr = window.devicePixelRatio || 1;

    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;

    const ctx = canvas.getContext("2d");
    ctx.scale(dpr, dpr);

    const width = rect.width;
    const height = rect.height;

    const left = 35;
    const right = width - 8;
    const top = 10;
    const bottom = height - 25;

    const chartWidth = right - left;
    const chartHeight = bottom - top;

    ctx.clearRect(0, 0, width, height);

    // Horizontal grid and labels
    ctx.font = "9px Arial";
    ctx.fillStyle = "#8995a8";
    ctx.textAlign = "right";

    for (let value = 0; value <= 100; value += 20) {
        const y = bottom - chartHeight * value / 100;

        ctx.strokeStyle = "#edf0f5";
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(left, y);
        ctx.lineTo(right, y);
        ctx.stroke();

        ctx.fillText(value, left - 9, y + 3);
    }

    // X axis labels
    ctx.textAlign = "center";
    ctx.fillStyle = "#8995a8";

    const labels = ["-30s", "-25s", "-20s", "-15s", "-10s", "-5s", "Now"];

    labels.forEach((label, index) => {
        const x = left + chartWidth * index / 6;
        ctx.fillText(label, x, height - 6);
    });

    // Traffic sample line
    const points = state.samples.map((value, index) => ({
        x: left + chartWidth * index / (state.samples.length - 1),
        y: bottom - chartHeight * value / 100
    }));

    ctx.beginPath();

    points.forEach((point, index) => {
        if (index === 0) {
            ctx.moveTo(point.x, point.y);
        } else {
            ctx.lineTo(point.x, point.y);
        }
    });

    ctx.strokeStyle = "#3976e8";
    ctx.lineWidth = 2;
    ctx.stroke();

    // Fill under line
    ctx.lineTo(right, bottom);
    ctx.lineTo(left, bottom);
    ctx.closePath();

    ctx.fillStyle = "rgba(57, 118, 232, 0.08)";
    ctx.fill();

    // Last sample marker
    const last = points[points.length - 1];

    ctx.beginPath();
    ctx.arc(last.x, last.y, 4, 0, Math.PI * 2);
    ctx.fillStyle = "#3976e8";
    ctx.fill();
}

function stopDemo(message = "Demo stopped") {
    state.running = false;

    clearInterval(state.timer);
    clearInterval(state.sampleTimer);

    state.timer = null;
    state.sampleTimer = null;

    $("startBtn").textContent = "▶ Start 5-Minute Live Demo";

    updateRunStatus("● DEMO STOPPED");
    updateActivity(message);
}

function startDemo() {
    if (state.running) return;

    state.running = true;

    updateRunStatus("● SIMULATION RUNNING");
    updateActivity("Live demo started");

    updateTimer();
    addSample();

    state.timer = setInterval(() => {
        state.elapsed++;

        updateTimer();

        if (state.elapsed >= 300) {
            stopDemo("Five-minute demo completed");
            updateRunStatus("● DEMO COMPLETED");
            showToast("Five-minute demo completed");
        }
    }, 1000);

    state.sampleTimer = setInterval(() => {
        const random = Math.random();

        let level;

        if (random < 0.30) {
            level = "LOW";
        } else if (random < 0.80) {
            level = "MEDIUM";
        } else {
            level = "HIGH";
        }

        setLevel(level);
        addSample();

    }, 2000);

    showToast("Live simulation started");
}

// Start, stop and reset
$("startBtn").addEventListener("click", startDemo);

$("stopBtn").addEventListener("click", () => {
    if (!state.running) {
        showToast("Demo is not running");
        return;
    }

    stopDemo();
    showToast("Simulation stopped");
});

$("resetBtn").addEventListener("click", () => {
    stopDemo("Demo reset");

    state.elapsed = 0;
    state.totalRequests = 0;
    state.samples = Array(30).fill(35);

    $("totalRequests").textContent = "0";

    setLevel("MEDIUM");
    updateTimer();
    updateRunStatus("● DEMO READY");

    drawChart();
    showToast("Dashboard reset");
});

// Open simulator button
$("openSimulator").addEventListener("click", () => {
    $("trafficChart").scrollIntoView({
        behavior: "smooth",
        block: "center"
    });
});

// Sidebar navigation
document.querySelectorAll(".nav-item").forEach(button => {
    button.addEventListener("click", () => {

        document.querySelectorAll(".nav-item")
            .forEach(item => item.classList.remove("active"));

        button.classList.add("active");

        const page = button.dataset.page;

        $("breadcrumb").textContent = page;
        $("pageTitle").textContent =
            page === "Overview" ? "System overview" : page;

        if (page !== "Overview") {
            showToast(`${page} section selected`);
        }
    });
});

// Initial dashboard
setLevel("MEDIUM");
updateTimer();
drawChart();

window.addEventListener("resize", drawChart);
