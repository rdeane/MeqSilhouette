===============
RIME Components
===============

The various components of the Radio Interferometer Measurement Equation (RIME) (`Smirnov 2011 <https://arxiv.org/abs/1101.1764>`_, and references therein) are
implemented manually in MeqSilhouette. Currently, the following RIME terms are implemented:

.. math::

    V_{pq} = G_{p} \left(\sum_{s} E_{ps} K_{ps} B_{s} K_{qs}^H E_{qs}^H \right) G_{q}^H

where for source :math:`s` and antenna :math:`p`, :math:`G_{p}` and :math:`E_{ps}` represent the direction-independent effects (DIEs) and direction-dependent effects (DDEs) respectively,
:math:`K_{ps}` represents the scalar phase delay matrix, and :math:`B_{s}` represents the brightness matrix.

.. todo:: Describe the various Jones matrices that are implemented in MeqSilhouette. For now, refer to Natarajan et al., in prep.
