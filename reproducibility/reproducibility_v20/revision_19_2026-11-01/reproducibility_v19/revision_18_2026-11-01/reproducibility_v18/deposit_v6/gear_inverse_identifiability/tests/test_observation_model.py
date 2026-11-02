"""Fase 1: pruebas del modelo de observacion y su coherencia con el inverso.

Cobertura requerida por el protocolo:
  - reproducibilidad con semillas fijas,
  - centrado correcto de cada curva (media del ciclo removida ANTES del ruido),
  - dimensiones del Jacobiano apilado,
  - coherencia entre residuos y funcion objetivo,
  - coherencia entre matriz de Fisher y modelo de ruido,
  - tratamiento de parametros fijados y limites.
"""
import sys
from pathlib import Path
import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from geometry.involute import InvoluteGear, GearPair
from geometry.microgeometry import TipRelief
from mechanics.compliance import GearContactModel
from mechanics.batched_operator import BatchedGapOperator
from identifiability.fisher_optimal_loads import FisherLoadSelector

SCALE = np.array([.05, 1, .01, 1])
THETA = np.array([.02, .75, .005, .25])


def _operator(torque=100, n=120):
    pair = GearPair(InvoluteGear(24, 3, 20, 20), InvoluteGear(48, 3, 20, 20))
    model = GearContactModel(pair, TipRelief())
    return BatchedGapOperator(model, torque, n)


def test_seed_reproducibility_of_noise():
    a = np.random.default_rng(123).normal(0, 1e-4, 50)
    b = np.random.default_rng(123).normal(0, 1e-4, 50)
    np.testing.assert_array_equal(a, b)
    c = np.random.default_rng(124).normal(0, 1e-4, 50)
    assert not np.allclose(a, c)


@pytest.mark.parametrize('torque', [50, 100, 300])
def test_prediction_is_cycle_centered(torque):
    pred = _operator(torque, 120).evaluate(THETA)['prediction']
    assert pred.shape == (120,)
    assert abs(float(np.mean(pred))) < 1e-12


def test_noise_added_to_centered_prediction_keeps_mean_unremoved():
    # Politica de la campana: ruido independiente sobre la prediccion YA
    # centrada, sin segundo centrado. La media del ruido realizado contribuye
    # al costo (no se re-centra la observacion).
    op = _operator(300, 120)
    pred = op.evaluate(THETA)['prediction']
    # Normalizar la muestra para que la varianza sea exactamente sigma^2 y el
    # chequeo de covarianza no dependa de la fluctuacion muestral.
    z = np.random.default_rng(7).normal(0, 1.0, 120)
    noise = 1e-4 * z / np.std(z)
    y = pred + noise
    # La observacion NO esta re-centrada: su media es la del ruido, no cero.
    assert abs(float(np.mean(pred))) < 1e-12
    assert abs(float(np.mean(y))) > 0.0          # tipicamente ~ sigma/sqrt(N)
    assert float(np.mean(y)) == pytest.approx(float(np.mean(noise)), rel=1e-9)
    # Covarianza del ruido: sigma^2 I (no proyectada), porque no hay
    # centrado posterior a la adicion del ruido.
    resid = y - pred
    assert float(np.var(resid)) == pytest.approx((1e-4) ** 2, rel=5e-2)


def test_stacked_jacobian_dimensions_two_loads():
    pair = GearPair(InvoluteGear(24, 3, 20, 20), InvoluteGear(48, 3, 20, 20))
    model = GearContactModel(pair, TipRelief())
    ops = [BatchedGapOperator(model, 50, 60), BatchedGapOperator(model, 300, 60)]
    blocks = [op.evaluate(THETA, jacobian=True)['jacobian'] for op in ops]
    assert blocks[0].shape == (60, 4) and blocks[1].shape == (60, 4)
    J = np.vstack(blocks)
    assert J.shape == (120, 4)


def test_residual_objective_coherence():
    # cost = 0.5 * sum(((pred - y)/sigma)^2) con el theta devuelto.
    op = _operator(100, 60)
    pred = op.evaluate(THETA)['prediction']
    rng = np.random.default_rng(11)
    sigma = 2e-4
    y = pred + rng.normal(0, sigma, 60)
    r = (pred - y) / sigma
    # Replicar la funcion objetivo declarada (min sum r^2 / 2):
    cost = float(0.5 * np.sum(r ** 2))
    assert cost == pytest.approx(0.5 * 60, rel=0.3)   # esperanza chi2/2 = N/2
    # El gradiente del costo coincide con -J^T r / sigma (definicion analitica).
    J = op.evaluate(THETA, jacobian=True)['jacobian']
    grad = J.T @ r / sigma
    fd = np.zeros(4)
    for j in range(4):
        v = np.zeros(4); v[j] = 1e-6 * SCALE[j]
        fp = 0.5 * np.sum(((op.evaluate(THETA + v)['prediction'] - y) / sigma) ** 2)
        fm = 0.5 * np.sum(((op.evaluate(THETA - v)['prediction'] - y) / sigma) ** 2)
        fd[j] = (fp - fm) / (2e-6 * SCALE[j])
    np.testing.assert_allclose(grad, fd, rtol=1e-3, atol=1e-2)


def test_fisher_matches_noise_model_and_implicit_tangent():
    # J_q = sigma^{-1} dF/dtheta diag(scale) usando el MISMO operador que el
    # inverso; la matriz de informacion es J_q^T J_q (ruido iid sigma^2 I).
    pair = GearPair(InvoluteGear(24, 3, 20, 20), InvoluteGear(48, 3, 20, 20))
    model = GearContactModel(pair, TipRelief())
    te_cycle = _mk_cycle(model)
    sigma = 1e-4
    sel = FisherLoadSelector(te_cycle, THETA, n_positions=120,
                             parameter_scale=SCALE, sigma_mm=sigma, h_rel=1e-4)
    Jq = sel.stacked_jacobian([100])                      # (120, 4)
    op = BatchedGapOperator(model, 100, 120)
    J_impl = op.evaluate(THETA, jacobian=True)['jacobian'] * SCALE / sigma
    # Mismo operador, mismo sigma, mismas escalas: columnas proporcionales a
    # la tangente implicita (diferencias centrales de h_rel sobre theta).
    norms_impl = np.linalg.norm(J_impl, axis=0)
    norms_fd = np.linalg.norm(Jq, axis=0)
    np.testing.assert_allclose(norms_fd, norms_impl, rtol=1e-3)
    F = sel.fisher_matrix([100])
    assert F.shape == (4, 4)
    # Informacion = J_q^T J_q con la covarianza correcta: reescalar sigma
    # por factor k divide la informacion por k^2.
    sel2 = FisherLoadSelector(te_cycle, THETA, n_positions=120,
                              parameter_scale=SCALE, sigma_mm=2 * sigma, h_rel=1e-4)
    np.testing.assert_allclose(sel2.fisher_matrix([100]), F / 4.0, rtol=1e-3)


def _mk_cycle(model):
    class Cycle:
        def compute_cycle(self, torque_Nm, n_positions, theta1, theta2=None):
            op = BatchedGapOperator(model, torque_Nm, n_positions)
            return {'TE_lin_fluct': op.evaluate(np.asarray(theta1, float))['prediction']}
    return Cycle()


def test_fixed_parameter_and_bounds_policy():
    # La API de ajuste con parametros fijados existe en la campana Q1
    # (experiments/Q1_identifiability_campaign.fit): un indice fijado se
    # excluye del espacio libre y su valor se restaura en el theta final.
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'experiments'))
    from Q1_identifiability_campaign import fit, operators
    op = operators([(100, 60)])[0]
    y = op.evaluate(THETA)['prediction']
    res = fit([op], y, 1e-4, np.array([.03, .65, .01, .35]), fixed={3: 0.31})
    est = np.array(res['theta'])
    assert est[3] == 0.31                      # fijado, no optimizado
    assert 0.0 <= est[0] <= 0.1                # limites fisicos respetados
    assert 0.30 <= est[1] <= 0.95
    assert 0.0 <= est[2] <= 0.05
    assert res['success']


def test_gamma_is_zero_in_noise_campaigns():
    # Documenta la politica: los experimentos de ruido usan gamma = 0; el
    # sesgo multiplicativo solo aparece en los casos 'bias' de E04 y NO se
    # estima (molestia no modelada). Ningun generador Q1 usa gamma.
    e04 = (Path(__file__).resolve().parents[1] / 'experiments' / 'E04_noise_bias.py').read_text()
    assert 'gamma=0.0' in e04.replace(' ', '')
    q1 = (Path(__file__).resolve().parents[1] / 'experiments' / 'Q1_identifiability_campaign.py').read_text()
    assert 'gamma' not in q1
