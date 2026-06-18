%% CE586 Earthquake Engineering - Assignment 4 (Q1)
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

EI_b = EI;                    % Beam EI for all Storys

%% =======================================================================
%% 2. QUESTION 1: STIFFNESS & DIFFERENTIAL EQUATION MATRICES
%% =======================================================================
% --- Flexurally Flexible Beams (6x6 Condensed to 3x3) ---
k_s = 12 * EI_c / h^3;        % Story lateral stiffnesses
Ktt = zeros(nF);              % Translational stiffness block
for s = 1:nF
    ft = s; fb = s - 1;
    Ktt(ft,ft) = Ktt(ft,ft) + k_s(s);
    if fb >= 1
        Ktt(fb,fb) = Ktt(fb,fb) + k_s(s);
        Ktt(ft,fb) = Ktt(ft,fb) - k_s(s);
        Ktt(fb,ft) = Ktt(fb,ft) - k_s(s);
    end
end

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

K_flex = Ktt - Kttheta * (Krr \ Kttheta'); % Static Condensation

fprintf('\nQ1: Stiffness Matrices (kN/m)\n');
fprintf('Case 2 (Flexible Beams - Condensed):\n'); disp(K_flex);

%% =======================================================================
%% 3. QUESTION 2: EIGENVALUE & RAYLEIGH DAMPING ANALYSIS
%% =======================================================================
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

% --- Flexible Beam Outputs ---
fprintf('\nQ2: MODAL PROPERTIES & DAMPING MATRICES (TOP Story NORMALIZATION)\n');
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
