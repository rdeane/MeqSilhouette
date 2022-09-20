===============
RIME Components
===============

The various components of the Radio Interferometer Measurement Equation (RIME) (`Smirnov 2011 <https://arxiv.org/abs/1101.1764>`_,
and references therein) are implemented in MeqSilhouette. The generic RIME is given by

.. math::

    V_{pq} = G_{p} \left(\sum_{s} E_{ps} K_{ps} B_{s} K_{qs}^H E_{qs}^H \right) G_{q}^H

where for source :math:`s` and antenna :math:`p`, :math:`G_{p}` and :math:`E_{ps}` represent the direction-independent effects (DIEs) and direction-dependent effects (DDEs) respectively,
:math:`K_{ps}` represents the scalar phase delay matrix, and :math:`B_{s}` represents the brightness matrix.

For more details, refer to Natarajan et al., (in prep).
