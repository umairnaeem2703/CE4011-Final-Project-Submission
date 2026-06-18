%% CE586 Earthquake Engineering - Assignment 4 (Q1 to Q4)
clear; clc; close all;

%% =======================================================================
%% 1. INPUT PARAMETERS (FULLY PARAMETRIC)
%% =======================================================================

% Geometry & Structural Properties
h        = 3;                 % m (Individual Story height)
L        = 4;                 % m (Bay width / Beam span)
nF       = 3;                 % Number of Storys
EI       = 3600;              % kNm^2 (Base flexural rigidity)
M_diag   = [20; 15; 15];      % tonnes (Story masses: [Story 1; Story 2; Story 3])
zeta     = 0.05;              % Damping ratio for Rayleigh & Response Spectra (5%)

% Ground Motion File Configuration
gm_filename = 'ground_motion.txt'; % Name of the input ground motion file

% --- Automatic Array Generation Based on Inputs ---
Story_h = (1:nF)' * h;        % Cumulative height of each Story from base [3; 6; 9]
M       = diag(M_diag);       % Mass Matrix
W_tot   = sum(M_diag) * 9.81; % Total structural weight (kN)

% Column EI values per Story (Sum of both columns per Story)
EI_c = [4*EI; 4*EI; 2*EI];

EI_b = EI;                    % Beam EI for all Storys (Case 2)

%% =======================================================================
%% 2. QUESTION 1: STIFFNESS & DIFFERENTIAL EQUATION MATRICES
%% =======================================================================
% --- CASE 1: Flexurally Rigid Beams ---
k_s = 12 * EI_c / h^3;        % Story lateral stiffnesses
K_rigid = zeros(nF);
for s = 1:nF
    ft = s; fb = s - 1;
    K_rigid(ft,ft) = K_rigid(ft,ft) + k_s(s);
    if fb >= 1
        K_rigid(fb,fb) = K_rigid(fb,fb) + k_s(s);
        K_rigid(ft,fb) = K_rigid(ft,fb) - k_s(s);
        K_rigid(fb,ft) = K_rigid(fb,ft) - k_s(s);
    end
end

% --- CASE 2: Flexurally Flexible Beams (6x6 Condensed to 3x3) ---
Kttheta = zeros(nF);          % Translational-Rotational coupling
Krr     = zeros(nF);          % Rotational stiffness block

for s = 1:nF
    ft = s; fb = s - 1;
    cf = 6 * EI_c(s) / h^2;   % Column shear-rotation coupling coefficient

    Kttheta(ft, ft) = Kttheta(ft, ft) - cf;
    if fb >= 1
        Kttheta(fb, ft) = Kttheta(fb, ft) + cf;
        Kttheta(ft, fb) = Kttheta(ft, fb) - cf;
        Kttheta(fb, fb) = Kttheta(fb, fb) + cf;
    end
end

for s = 1:nF
    ft = s; fb = s - 1;
    Krr(ft, ft) = Krr(ft, ft) + 4 * EI_c(s) / h;
    if fb >= 1
        Krr(fb, fb) = Krr(fb, fb) + 4 * EI_c(s) / h;
        Krr(ft, fb) = Krr(ft, fb) + 2 * EI_c(s) / h;
        Krr(fb, ft) = Krr(fb, ft) + 2 * EI_c(s) / h;
    end
end

% Beam contributions: Kb = 12*EI_b/L per Story (both joints rotating equally)
Kb = 12 * EI_b / L;
for i = 1:nF
    Krr(i,i) = Krr(i,i) + Kb;
end

K_flex = K_rigid - Kttheta * (Krr \ Kttheta'); % Static Condensation

fprintf('\nQ1: Stiffness Matrices (kN/m)\n');
fprintf('Case 1 (Rigid Beams):\n'); disp(K_rigid);
fprintf('Case 2 (Flexible Beams - Condensed):\n'); disp(K_flex);

%% =======================================================================
%% 3. QUESTION 2: EIGENVALUE & RAYLEIGH DAMPING ANALYSIS
%% =======================================================================
% -----------------------------------------------------------------------
% CASE 1: Rigid Beams Eigenvalue and Damping Analysis
% -----------------------------------------------------------------------
[V_rigid, D_eig_rigid] = eig(K_rigid, M);
lambda_rigid           = diag(D_eig_rigid);
[lambda_rigid, idx_r]  = sort(lambda_rigid); % Sort ascending
V_rigid                = V_rigid(:, idx_r);
omega_rigid            = sqrt(lambda_rigid);
T_rigid                = 2 * pi ./ omega_rigid;

% Normalize mode shapes to topmost Story
Phi_rigid              = V_rigid ./ V_rigid(nF, :);

% Rayleigh Damping for Case 1
w1_r = omega_rigid(1); w2_r = omega_rigid(2);
alpha_rigid = zeta * (2 * w1_r * w2_r) / (w1_r + w2_r);
beta_rigid  = zeta * 2 / (w1_r + w2_r);
C_rigid     = alpha_rigid * M + beta_rigid * K_rigid;

% -----------------------------------------------------------------------
% CASE 2: Flexible Beams Eigenvalue and Damping Analysis
% -----------------------------------------------------------------------
[V_flex, D_eig_flex] = eig(K_flex, M);
lambda_flex          = diag(D_eig_flex);
[lambda_flex, idx_f] = sort(lambda_flex); % Sort ascending
V_flex               = V_flex(:, idx_f);
omega_flex           = sqrt(lambda_flex);
T_flex               = 2 * pi ./ omega_flex;

% Normalize mode shapes to topmost Story
Phi_flex             = V_flex ./ V_flex(nF, :);

% Rayleigh Damping for Case 2
w1_f = omega_flex(1); w2_f = omega_flex(2);
alpha_flex = zeta * (2 * w1_f * w2_f) / (w1_f + w2_f);
beta_flex  = zeta * 2 / (w1_f + w2_f);
C_flex     = alpha_flex * M + beta_flex * K_flex;

% --- Separation of Case 1 and Case 2 Outputs ---
fprintf('\nQ2: MODAL PROPERTIES & DAMPING MATRICES (TOP Story NORMALIZATION)\n');
fprintf('\n>>> CASE 1: RIGID BEAMS <<<\n');
fprintf('Mode | lambda (rad^2/s^2) | omega (rad/s) | T (s)\n');
for n = 1:nF
    fprintf('  %d  |     %9.3f      |    %7.3f    | %.3f\n', n, lambda_rigid(n), omega_rigid(n), T_rigid(n));
end
fprintf('\nMode Shapes (Phi_rigid):\n'); disp(Phi_rigid);
fprintf('Rayleigh Damping Coefficients:\n');
fprintf('  alpha = %.5f s^-1\n', alpha_rigid);
fprintf('  beta  = %.7f s\n', beta_rigid);
fprintf('\nRayleigh Damping Matrix C_rigid (kN.s/m):\n'); disp(C_rigid);

fprintf('\n>>> CASE 2: FLEXIBLE BEAMS <<<\n');
fprintf('Mode | lambda (rad^2/s^2) | omega (rad/s) | T (s)\n');
for n = 1:nF
    fprintf('  %d  |     %9.3f      |    %7.3f    | %.3f\n', n, lambda_flex(n), omega_flex(n), T_flex(n));
end
fprintf('\nMode Shapes (Phi_flex):\n'); disp(Phi_flex);
fprintf('Rayleigh Damping Coefficients:\n');
fprintf('  alpha = %.5f s^-1\n', alpha_flex);
fprintf('  beta  = %.7f s\n', beta_flex);
fprintf('\nRayleigh Damping Matrix C_flex (kN.s/m):\n'); disp(C_flex);

%% =======================================================================
%% 4. QUESTION 3: MODAL PROPERTIES & RESPONSE HIStory ANALYSIS (RHA)
%% =======================================================================
% Note: Per Q2/Q3 instructions, dynamics proceed using Case 1 (Rigid)
T     = T_rigid;
omega = omega_rigid;
Phi   = Phi_rigid;

if ~exist(gm_filename, 'file')
    error('Ground motion file "%s" not found. Please verify paths.', gm_filename);
end
gm_data = load(gm_filename);
t       = gm_data(:, 1);
ug_ddot = gm_data(:, 2) / 100.0;  % Convert cm/s^2 to m/s^2
dt      = t(2) - t(1);
N_steps = length(t);

iota   = ones(nF, 1);
Mn     = zeros(nF, 1); Ln = zeros(nF, 1); Gamma = zeros(nF, 1);
M_star = zeros(nF, 1); h_star = zeros(nF, 1);
D      = zeros(nF, N_steps);       % Modal SDOF Displacement trace
max_D   = zeros(nF, 1);             % Peak absolute values of SDOF displacements
t_max_D = zeros(nF, 1);             % Time of occurrence for SDOF displacement peaks

% Calculate Modal Properties & Solve SDOF Equations via Newmark Linear Acceleration
for n = 1:nF
    Mn(n)    = Phi(:,n)' * M * Phi(:,n);
    Ln(n)    = Phi(:,n)' * M * iota;
    Gamma(n) = Ln(n) / Mn(n);

    % Effective Modal Parameters (Q3f)
    M_star(n) = (Ln(n)^2) / Mn(n);
    L_theta   = Phi(:,n)' * M * Story_h;
    h_star(n) = L_theta / Ln(n);

    % Newmark Constant Average Acceleration Integration Parameters
    wn    = omega(n);
    c_n   = 2 * zeta * wn;
    k_n   = wn^2;
    p     = -ug_ddot; 

    % Initial states (At rest setup)
    D(n, 1) = 0; D_dot = 0; D_ddot = p(1);
    k_hat   = k_n + (2/dt)*c_n + (4/(dt^2));
    a_coeff = (4/dt) + 2*c_n;
    b_coeff = 2;

    for i = 1:(N_steps-1)
        dp     = p(i+1) - p(i);
        dp_hat = dp + a_coeff*D_dot + b_coeff*D_ddot;
        du     = dp_hat / k_hat;
        dv     = (2/dt)*du - 2*D_dot;
        da     = (4/(dt^2))*du - (4/dt)*D_dot - 2*D_ddot;
        
        D(n, i+1) = D(n, i) + du;
        D_dot     = D_dot + dv;
        D_ddot    = D_ddot + da;
    end

    % Extract Maxima and Time of Occurrence (Q3b)
    [max_D(n), peak_idx] = max(abs(D(n, :)));
    t_max_D(n) = t(peak_idx);
end

% -----------------------------------------------------------------------
% QUESTION 3c: Story DISPLACEMENTS & Story DRIFTS
% -----------------------------------------------------------------------
% Reconstruct physical MDOF displacement histories: u(t) = sum( Gamma_n * Phi_n * D_n(t) )
u_rha = zeros(nF, N_steps);
f_rha = zeros(nF, N_steps);
for n = 1:nF
    u_rha = u_rha + Gamma(n) * Phi(:,n) * D(n, :);
    f_rha = f_rha + Gamma(n) * M * Phi(:,n) * (omega(n)^2) * D(n, :);
end

% Peak absolute displacements
RHA_u_max  = max(abs(u_rha), [], 2);

% Calculate Story relative drift histories (Delta_i(t))
Delta = zeros(nF, N_steps);
Delta(1, :) = u_rha(1, :);                              
for i = 2:nF
    Delta(i, :) = u_rha(i, :) - u_rha(i-1, :);          
end

% Extract maximum values and times of occurrence for drifts
max_drift   = zeros(nF, 1);
t_max_drift = zeros(nF, 1);
for i = 1:nF
    [max_drift(i), drift_peak_idx] = max(abs(Delta(i, :)));
    t_max_drift(i) = t(drift_peak_idx);
end

% -----------------------------------------------------------------------
% QUESTION 3d, 3e, 3f: FORCE-BASED RECONSTRUCTION & VERIFICATION
% -----------------------------------------------------------------------
% Story lateral force contributions and top-down shears
V3_rha = f_rha(3, :);
V2_rha = f_rha(3, :) + f_rha(2, :);
V1_rha = f_rha(3, :) + f_rha(2, :) + f_rha(1, :); % Base Shear
Mb_rha = sum(f_rha .* Story_h, 1);                 % Base Moment

% Extract maximum values and times of occurrence for shears
[RHA_V1_max, idx_V1] = max(abs(V1_rha)); t_max_V1 = t(idx_V1);
[RHA_V2_max, idx_V2] = max(abs(V2_rha)); t_max_V2 = t(idx_V2);
[RHA_V3_max, idx_V3] = max(abs(V3_rha)); t_max_V3 = t(idx_V3);

% Extract maximum overturning moment
[RHA_Mb_max, idx_Mb] = max(abs(Mb_rha)); t_max_Mb = t(idx_Mb);

% Verification using Invariant Effective Parameters (Part f SDOF formulation)
Vb_eff_hiStory = zeros(1, N_steps);
Mb_eff_hiStory = zeros(1, N_steps);
for n = 1:nF
    A_n_hiStory = (omega(n)^2) * D(n, :); % Pseudo-acceleration response hiStory
    Vb_eff_hiStory = Vb_eff_hiStory + M_star(n) * A_n_hiStory;
    Mb_eff_hiStory = Mb_eff_hiStory + h_star(n) * M_star(n) * A_n_hiStory;
end

% Extract peak invariant values
[Vb_eff_max, idx_Vb_eff] = max(abs(Vb_eff_hiStory)); t_max_Vb_eff = t(idx_Vb_eff);
[Mb_eff_max, idx_Mb_eff] = max(abs(Mb_eff_hiStory)); t_max_Mb_eff = t(idx_Mb_eff);

% Calculate relative differences
diff_Vb = max(abs(V1_rha - Vb_eff_hiStory));
diff_Mb = max(abs(Mb_rha - Mb_eff_hiStory));

%% --- ALPHABETICAL CONSOLIDATED OUTPUT WINDOW FOR Q3 ---
% Q3a
fprintf('\nQ3a: MODAL PROPERTIES (RIGID BEAMS)\n');
fprintf(' Mode |   L_n (t)   |   M_n (t)   |  Gamma_n  \n');
for n = 1:nF
    fprintf('  %d   |  %9.3f  |  %9.3f  |  %8.4f \n', n, Ln(n), Mn(n), Gamma(n));
end

% Q3b
fprintf('\nQ3b: EQUIVALENT SDOF SYSTEM PEAK RESPONSES (D_n(t))\n');
fprintf(' SDOF System | Period T_n (s) | Peak Absolute |D_n|_max (cm) | Time of Occurrence (s) \n');
for n = 1:nF
    fprintf('   Mode %d    |     %6.3f     |         %10.4f         |        %9.3f\n', n, T(n), max_D(n)*100, t_max_D(n));
end

% Q3c
fprintf('\nQ3c: PEAK Story RELATIVE DRIFT SUMMARY\n');
fprintf('  Story (i)   |    Max Drift Expression      | Peak Absolute Drift (cm)    | Time of Occurrence (s) \n');
fprintf('  1st Story   |          max |u1(t)|         |         %8.4f            |        %9.3f\n', max_drift(1)*100, t_max_drift(1));
fprintf('  2nd Story   |        max |u2(t) - u1(t)|   |         %8.4f            |        %9.3f\n', max_drift(2)*100, t_max_drift(2));
fprintf('  3rd Story   |        max |u3(t) - u2(t)|   |         %8.4f            |        %9.3f\n', max_drift(3)*100, t_max_drift(3));

% Q3d
fprintf('\nQ3d: PEAK Story SHEAR SUMMARY (RHA)\n');
fprintf('  Story (i)   |    Peak Absolute Shear V_i (kN)    | Time of Occurrence (s) \n');
fprintf('  1st (Base)  |             %10.2f             |        %9.3f\n', RHA_V1_max, t_max_V1);
fprintf('  2nd Story   |             %10.2f             |        %9.3f\n', RHA_V2_max, t_max_V2);
fprintf('  3rd (Roof)  |             %10.2f             |        %9.3f\n', RHA_V3_max, t_max_V3);

% Q3e
fprintf('\nQ3e: PEAK BASE OVERTURNING MOMENT SUMMARY (RHA)\n');
fprintf(' Parameter |   Peak Overturning Moment M_b (kNm)   | Time of Occurrence (s) \n');
fprintf('  Base M_b |                  %10.2f               |        %9.3f\n', RHA_Mb_max, t_max_Mb);

% Q3f (Parameters)
fprintf('\nQ3f: EFFECTIVE MODAL PARAMETERS (RIGID BEAMS)\n');
fprintf(' Mode |  M_star (t)  |  h_star (m) \n');
for n = 1:nF
    fprintf('  %d   |  %10.3f  |  %9.3f\n', n, M_star(n), h_star(n));
end

% Q3f (Verification)
fprintf('\nQ3f VERIFICATION: Story FORCES vs. INVARIANT MODAL SDOFs\n');
fprintf(' Parameter           | Story Force Summation | Invariant SDOF Formula | Abs Difference \n');
fprintf(' Peak Base Shear (kN)|       %9.2f       |       %9.2f        |    %10.2e\n', RHA_V1_max, Vb_eff_max, diff_Vb);
fprintf(' Peak Base Moment(kNm)|       %9.2f       |       %9.2f        |    %10.2e\n', RHA_Mb_max, Mb_eff_max, diff_Mb);
fprintf(' Verification Note: The dynamic response histories calculated by both methods\n');
fprintf(' are mathematically IDENTICAL. Grouping by spatial nodes (forces) and global energy\n');
fprintf(' metrics (modal parameters) are algebraically equivalent. (Diff = ~0)\n');

%% =======================================================================
%% 5. QUESTION 4: RESPONSE SPECTRUM & EQUIVALENT STATIC ANALYSES
%% =======================================================================
% --- Part (a): Generate Numerical Ground Motion Response Spectrum ---
T_grid  = 0.02:0.02:3.0;
Sa_spec = zeros(length(T_grid), 1);
Sd_spec = zeros(length(T_grid), 1);

for j = 1:length(T_grid)
    T_curr = T_grid(j); w_curr = 2*pi / T_curr;
    c_curr = 2 * zeta * w_curr; k_curr = w_curr^2;

    d_curr = 0; v_curr = 0; a_curr = -ug_ddot(1);
    k_hat   = k_curr + (2/dt)*c_curr + (4/(dt^2));
    a_coeff = (4/dt) + 2*c_curr;
    max_d   = 0;

    for i = 1:(N_steps-1)
        dp     = -ug_ddot(i+1) - (-ug_ddot(i));
        dp_hat = dp + a_coeff*v_curr + 2*a_curr;
        du     = dp_hat / k_hat;
        dv     = (2/dt)*du - 2*v_curr;
        da     = (4/(dt^2))*du - (4/dt)*v_curr - 2*a_curr;
        
        d_curr = d_curr + du; v_curr = v_curr + dv; a_curr = a_curr + da;
        if abs(d_curr) > max_d, max_d = abs(d_curr); end
    end
    Sa_spec(j) = (w_curr^2) * max_d;
    Sd_spec(j) = max_d; 
end

% Convert Sa_spec to units of g
Sa_spec_g = Sa_spec / 9.81;

% Interp specific spectral coordinates for structural periods
S_an = interp1(T_grid, Sa_spec, T);
S_dn = S_an ./ (omega.^2);
S_an_g = S_an / 9.81;

fprintf('\nQ4a: ELASTIC RESPONSE SPECTRA VALUES AT MODAL PERIODS\n');
fprintf(' Mode | Period T (s) | S_d (m) | S_a (g) \n');
for n = 1:nF
    fprintf('  %d   |    %6.3f    | %7.4f | %7.4f \n', n, T(n), S_dn(n), S_an_g(n));
end

% --- Part (b): Response Spectrum Analysis (RSA) Peak Extraction & Modal Combos ---
u_n_max   = zeros(nF, nF);
V_Story_n = zeros(nF, nF);
Mb_n_max  = zeros(nF, 1);

for n = 1:nF
    u_n_max(:, n) = Gamma(n) * Phi(:, n) * S_dn(n);
    f_n_max       = Gamma(n) * M * Phi(:, n) * S_an(n);
    
    % Store individual Story shears for each mode
    V_Story_n(3, n) = f_n_max(3);                             % Roof
    V_Story_n(2, n) = f_n_max(3) + f_n_max(2);                % Story 2
    V_Story_n(1, n) = f_n_max(3) + f_n_max(2) + f_n_max(1);   % Base
    
    Mb_n_max(n)   = sum(f_n_max .* Story_h);
end

% CQC Cross-Correlation Coefficient Matrix Setup
rho = zeros(nF, nF);
for i = 1:nF
    for n = 1:nF
        beta_in = omega(i) / omega(n);
        num = 8 * zeta^2 * (1 + beta_in) * beta_in^1.5;
        den = (1 - beta_in^2)^2 + 4 * zeta^2 * beta_in * (1 + beta_in)^2;
        rho(i, n) = num / den;
    end
end

RSA_u = zeros(nF, 3); 
RSA_V = zeros(nF, 3); 
RSA_Mb = zeros(1, 3);

for i = 1:nF
    % Modal combination for Story Displacements
    RSA_u(i, 1) = sum(abs(u_n_max(i, :)));                     % ABSSUM
    RSA_u(i, 2) = sqrt(sum(u_n_max(i, :).^2));                 % SRSS
    RSA_u(i, 3) = sqrt(abs(u_n_max(i, :) * rho * u_n_max(i, :)')); % CQC
    
    % Modal combination for Story Shears
    RSA_V(i, 1) = sum(abs(V_Story_n(i, :)));                     % ABSSUM
    RSA_V(i, 2) = sqrt(sum(V_Story_n(i, :).^2));                 % SRSS
    RSA_V(i, 3) = sqrt(abs(V_Story_n(i, :) * rho * V_Story_n(i, :)')); % CQC
end

% Modal combination for Base Moment
RSA_Mb(1) = sum(abs(Mb_n_max)); % ABSSUM
RSA_Mb(2) = sqrt(sum(Mb_n_max.^2)); % SRSS
RSA_Mb(3) = sqrt(abs(Mb_n_max' * rho * Mb_n_max)); % CQC

% --- Part (d): Equivalent Static Lateral Force Procedure (ESLFP) ---
T1 = T(1);
if T1 < 0.15
    A1_g = 0.4 + (1.0 - 0.4) * (T1 / 0.15);
elseif T1 <= 0.60
    A1_g = 1.0;
else
    A1_g = (0.6 / T1)^0.8;
end

Vb_eslfp = A1_g * W_tot;
Delta_Fn = 0; % neglected for this low-rise 3-story frame

f_eslfp  = (Vb_eslfp - Delta_Fn) * (M_diag .* Story_h) / sum(M_diag .* Story_h);
f_eslfp(nF) = f_eslfp(nF) + Delta_Fn;
Mb_eslfp = sum(f_eslfp .* Story_h);

%% =======================================================================
%% 6. CONSOLIDATED SUMMARY & COMPREHENSIVE OUTPUT WINDOW
%% =======================================================================
RHA_V_max = [RHA_V1_max; RHA_V2_max; RHA_V3_max]; % Vector array of RHA Story shears
eslfp_V   = [sum(f_eslfp); f_eslfp(2)+f_eslfp(3); f_eslfp(3)]; % ESLFP Shears

% -----------------------------------------------------------------------
% Q4c: Comparison Table with Absolute Percentage Differences
% -----------------------------------------------------------------------
fprintf('\nQ4c: COMPARISON OF RHA AND RSA RESPONSE QUANTITIES (ABSOLUTE PERCENTAGE DIFFERENCES)\n');
fprintf(' Response Parameter                    | RHA Exact(Q3) | RSA(ABSSUM) | Abs %% Diff |  RSA(SRSS)  | Abs %% Diff |  RSA(CQC)  | Abs %% Diff \n');
fprintf('---------------------------------------|---------------|-------------|------------|-------------|------------|------------|------------\n');

% Displacements
for i = 1:nF
    rha = RHA_u_max(i)*100;
    abs_v = RSA_u(i,1)*100; ad = abs((abs_v - rha)/rha * 100);
    srs_v = RSA_u(i,2)*100; sd = abs((srs_v - rha)/rha * 100);
    cqc_v = RSA_u(i,3)*100; cd = abs((cqc_v - rha)/rha * 100);
    
    lbl = sprintf('Story %d Disp. (u_%d, cm)', i, i);
    fprintf(' %-37s | %13.4f | %11.4f | %10.2f | %11.4f | %10.2f | %10.4f | %10.2f \n', ...
        lbl, rha, abs_v, ad, srs_v, sd, cqc_v, cd);
end

% Story Shears
for i = 1:nF
    rha = RHA_V_max(i);
    abs_v = RSA_V(i,1); ad = abs((abs_v - rha)/rha * 100);
    srs_v = RSA_V(i,2); sd = abs((srs_v - rha)/rha * 100);
    cqc_v = RSA_V(i,3); cd = abs((cqc_v - rha)/rha * 100);
    
    if i == 1
        lbl = 'Base Shear (V_1, kN)';
    else
        lbl = sprintf('Story %d Shear (V_%d, kN)', i, i);
    end
    fprintf(' %-37s | %13.2f | %11.2f | %10.2f | %11.2f | %10.2f | %10.2f | %10.2f \n', ...
        lbl, rha, abs_v, ad, srs_v, sd, cqc_v, cd);
end

% Base Moment
rha = RHA_Mb_max;
abs_v = RSA_Mb(1); ad = abs((abs_v - rha)/rha * 100);
srs_v = RSA_Mb(2); sd = abs((srs_v - rha)/rha * 100);
cqc_v = RSA_Mb(3); cd = abs((cqc_v - rha)/rha * 100);

lbl = 'Base Overturning Moment (M_b, kNm)';
fprintf(' %-37s | %13.2f | %11.2f | %10.2f | %11.2f | %10.2f | %10.2f | %10.2f \n', ...
    lbl, rha, abs_v, ad, srs_v, sd, cqc_v, cd);

% -----------------------------------------------------------------------
% Q4d: ESLFP Output
% -----------------------------------------------------------------------
fprintf('\nQ4d: EQUIVALENT STATIC LATERAL FORCE PROCEDURE (ESLFP)\n');
fprintf(' Base Shear (V_b):               %9.2f kN\n', Vb_eslfp);
fprintf(' Base Overturning Moment (M_b):  %9.2f kNm\n', Mb_eslfp);

% -----------------------------------------------------------------------
% Q4e: Comparison Table with Percentage Differences (Signed)
% -----------------------------------------------------------------------
fprintf('\nQ4e: COMPARISON OF RHA, RSA, AND ESLFP (PERCENTAGE DIFFERENCES)\n');
fprintf(' Response Parameter                    | RHA Exact(Q3) | RSA(ABSSUM) |   %% Diff   |  RSA(SRSS)  |   %% Diff   |  RSA(CQC)  |   %% Diff   | ESLFP(Code) |   %% Diff   \n');
fprintf('---------------------------------------|---------------|-------------|------------|-------------|------------|------------|------------|-------------|------------\n');

% Displacements
for i = 1:nF
    rha = RHA_u_max(i)*100;
    abs_v = RSA_u(i,1)*100; ad = (abs_v - rha)/rha * 100;
    srs_v = RSA_u(i,2)*100; sd = (srs_v - rha)/rha * 100;
    cqc_v = RSA_u(i,3)*100; cd = (cqc_v - rha)/rha * 100;
    
    lbl = sprintf('Story %d Disp. (u_%d, cm)', i, i);
    fprintf(' %-37s | %13.4f | %11.4f | %10.2f | %11.4f | %10.2f | %10.4f | %10.2f |     N/A     |     N/A    \n', ...
        lbl, rha, abs_v, ad, srs_v, sd, cqc_v, cd);
end

% Story Shears
for i = 1:nF
    rha = RHA_V_max(i);
    abs_v = RSA_V(i,1); ad = (abs_v - rha)/rha * 100;
    srs_v = RSA_V(i,2); sd = (srs_v - rha)/rha * 100;
    cqc_v = RSA_V(i,3); cd = (cqc_v - rha)/rha * 100;
    esl_v = eslfp_V(i); ed = (esl_v - rha)/rha * 100;
    
    if i == 1
        lbl = 'Base Shear (V_1, kN)';
    else
        lbl = sprintf('Story %d Shear (V_%d, kN)', i, i);
    end
    fprintf(' %-37s | %13.2f | %11.2f | %10.2f | %11.2f | %10.2f | %10.2f | %10.2f | %11.2f | %10.2f \n', ...
        lbl, rha, abs_v, ad, srs_v, sd, cqc_v, cd, esl_v, ed);
end

% Base Moment
rha = RHA_Mb_max;
abs_v = RSA_Mb(1); ad = (abs_v - rha)/rha * 100;
srs_v = RSA_Mb(2); sd = (srs_v - rha)/rha * 100;
cqc_v = RSA_Mb(3); cd = (cqc_v - rha)/rha * 100;
esl_v = Mb_eslfp;  ed = (esl_v - rha)/rha * 100;

lbl = 'Base Overturning Moment (M_b, kNm)';
fprintf(' %-37s | %13.2f | %11.2f | %10.2f | %11.2f | %10.2f | %10.2f | %10.2f | %11.2f | %10.2f \n\n', ...
    lbl, rha, abs_v, ad, srs_v, sd, cqc_v, cd, esl_v, ed);

%% =======================================================================
%% 7. GRAPHICAL DISPLAY GENERATION
%% =======================================================================
% The assignment explicitly asks for the following plotted histories:
% Q3b: D_n(t), n = 1-3
% Q3c: u_i(t), i = 1-3, and story drift histories
% Q3d: V_i(t), i = 1-3
% Q3e: M_b(t)
% Q4a: 5% elastic response spectrum from the assigned ground motion

% Figure 1: Equivalent SDOF Displacement Histories (Q3 part b)
figure('Name', 'Q3b: SDOF Displacement Responses', 'Color', 'w');
for n = 1:nF
    subplot(nF, 1, n);
    plot(t, D(n, :)*100, 'b-', 'LineWidth', 1.2);
    grid on;
    xlabel('Time (s)');
    ylabel(sprintf('D_%d(t) (cm)', n));
    title(sprintf('Q3b: Equivalent SDOF Displacement History — Mode %d (T_%d = %.3f s)', n, n, T(n)));
end

% Figure 2: Floor Displacement Histories (Q3 part c)
figure('Name', 'Q3c: Floor Displacement Histories', 'Color', 'w');
plot(t, u_rha(1, :)*100, 'b-', 'LineWidth', 1.2); hold on;
plot(t, u_rha(2, :)*100, 'r-', 'LineWidth', 1.2);
plot(t, u_rha(3, :)*100, 'g-', 'LineWidth', 1.2);
grid on;
xlabel('Time (s)');
ylabel('Floor Displacement u_i(t) (cm)');
title('Q3c: Floor Displacement Response Histories (RHA)');
legend('Floor 1: u_1(t)', 'Floor 2: u_2(t)', 'Floor 3: u_3(t)', 'Location', 'Best');

% Figure 3: Relative Story Drift Histories (Q3 part c)
figure('Name', 'Q3c: Story Drift Histories', 'Color', 'w');
plot(t, Delta(1, :)*100, 'b-', 'LineWidth', 1.2); hold on;
plot(t, Delta(2, :)*100, 'r-', 'LineWidth', 1.2);
plot(t, Delta(3, :)*100, 'g-', 'LineWidth', 1.2);
grid on;
xlabel('Time (s)');
ylabel('Story Drift \Delta_i(t) (cm)');
title('Q3c: Relative Story Drift Histories (RHA)');
legend('Story 1: \Delta_1(t)=u_1(t)', 'Story 2: \Delta_2(t)=u_2(t)-u_1(t)', ...
       'Story 3: \Delta_3(t)=u_3(t)-u_2(t)', 'Location', 'Best');

% Figure 4: Story Shear Histories (Q3 part d)
figure('Name', 'Q3d: Story Shear Histories', 'Color', 'w');
plot(t, V1_rha, 'b-', 'LineWidth', 1.2); hold on;
plot(t, V2_rha, 'r-', 'LineWidth', 1.2);
plot(t, V3_rha, 'g-', 'LineWidth', 1.2);
grid on;
xlabel('Time (s)');
ylabel('Story Shear V_i(t) (kN)');
title('Q3d: Story Shear Response Histories (RHA)');
legend('Story 1: V_1(t) / Base Shear', 'Story 2: V_2(t)', 'Story 3: V_3(t)', 'Location', 'Best');

% Figure 5: Base Overturning Moment History (Q3 part e) and Q3f Verification
figure('Name', 'Q3e & Q3f: Base Overturning Moment History', 'Color', 'w');
plot(t, Mb_rha, 'b-', 'LineWidth', 1.2); hold on;
plot(t, Mb_eff_hiStory, 'r--', 'LineWidth', 1.2);
grid on;
xlabel('Time (s)');
ylabel('Base Overturning Moment M_b(t) (kNm)');
title('Q3e: Base Overturning Moment History with Q3f Invariant SDOF Verification');
legend('M_b(t) from Story Force Summation', 'M_b(t) from Effective Modal Parameters', 'Location', 'Best');

% Figure 6: Numerical Response Spectrum vs System Eigenperiods (Q4 part a)
figure('Name', 'Q4a: Ground Motion Elastic Response Spectrum', 'Color', 'w');
subplot(2, 1, 1);
plot(T_grid, Sa_spec_g, 'b-', 'LineWidth', 1.5); hold on; grid on;
plot(T, S_an_g, 'ro', 'MarkerFaceColor', 'r', 'MarkerSize', 7);
xlabel('Period T (sec)');
ylabel('Spectral Pseudo-Acceleration S_a (g)');
title('Q4a: Elastic Pseudo-Acceleration Response Spectrum (\zeta = 5%)');
legend('Calculated Ground-Motion Spectrum', 'Structural Eigenperiods (T_1, T_2, T_3)', 'Location', 'Best');

subplot(2, 1, 2);
plot(T_grid, Sd_spec, 'b-', 'LineWidth', 1.5); hold on; grid on;
plot(T, S_dn, 'ro', 'MarkerFaceColor', 'r', 'MarkerSize', 7);
xlabel('Period T (sec)');
ylabel('Spectral Displacement S_d (m)');
title('Q4a: Elastic Spectral Displacement Response Spectrum (\zeta = 5%)');
legend('Calculated Ground-Motion Spectrum', 'Structural Eigenperiods (T_1, T_2, T_3)', 'Location', 'Best');
