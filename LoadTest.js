import http from 'k6/http';
import { check, sleep } from 'k6';

// ======= Configuration =======
const USERS_PER_STEP = 5;              // Users added per ramp step
const STEP_DURATION = '30s';           // Duration of each ramp step
const MAX_USERS = 25;                  // Peak concurrent users
const HOLD_DURATION_AT_PEAK = '1h';    // Hold time after max users reached
const TEST_URL = 'https://your-api-domain.com/healthz'; // Endpoint to test
const AUTH_TOKEN = 'your_bearer_token_here'; // Replace with your actual token
// =============================

// Generate ramp-up stages
const rampStages = [];
for (let users = USERS_PER_STEP; users <= MAX_USERS; users += USERS_PER_STEP) {
  rampStages.push({ duration: STEP_DURATION, target: users });
}
rampStages.push({ duration: HOLD_DURATION_AT_PEAK, target: MAX_USERS });
rampStages.push({ duration: STEP_DURATION, target: 0 });

export const options = {
  stages: rampStages,
  thresholds: {
    http_req_duration: ['p(95)<300'],
    http_req_failed: ['rate<0.01'],
  },
};

export default function () {
  const headers = {
    Authorization: `Bearer ${AUTH_TOKEN}`,
    'Content-Type': 'application/json',
  };

  const res = http.get(TEST_URL, { headers });

  console.log(`VU ${__VU} | Iteration ${__ITER} | Status: ${res.status}`);

  check(res, {
    'status is 200': (r) => r.status === 200,
  });

  sleep(1);
}
