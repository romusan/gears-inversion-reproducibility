"""Evidence screening: a public TE file alone does not validate relief inversion."""
import csv,hashlib,json
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parent


def main():
    sources=[
        dict(id='P01',title='Transmission Error Compensation for Industrial Robots Using Fourier Series',
            url='https://darus.uni-stuttgart.de/dataset.xhtml?persistentId=doi:10.18419/DARUS-5760',
            language='English',evidence='Repository API metadata + original experimental CSV sample(s)',
            measured_TE='yes',relief_of_same_gear_documented='not established',
            decision='INELIGIBLE for direct spur-relief inversion: robot gearbox system, no verified matching spur geometry or relief truth. Useful only as a separate signal-processing dataset.',
            license='CC BY 4.0'),
        dict(id='P02',title='Data/code: profile-shift coefficients and nonlinear dynamic spur-gear response',
            url='https://data.mendeley.com/datasets/82xmwb5pvs/1',language='English',
            evidence='Primary repository description',measured_TE='no: numerical data',relief_of_same_gear_documented='not dedendum relief',
            decision='INELIGIBLE for experimental validation; numerical cross-model resource only.',license='CC BY 4.0'),
        dict(id='P03',title='Analysis of gear TE considering measured tooth profile errors',
            url='https://doi.org/10.1038/s41598-025-90010-6',language='English',
            evidence='Downloaded full text R07; Data availability section',measured_TE='published experimental comparisons',
            relief_of_same_gear_documented='helical measured profiles in publication; no downloaded raw profile/TE pairing',
            decision='PROMISING reference, but raw data are available on reasonable request, not a verified public download. Helical operator required.',license='See article and any future data licence separately'),
        dict(id='P04',title='Static/dynamic TE of helical pairs with various tooth modifications',
            url='https://doi.org/10.1115/1.4043586',language='English',
            evidence='Verified metadata/abstract only; no full text or raw dataset obtained',
            measured_TE='reported in abstract',relief_of_same_gear_documented='reported modifications; raw pairing not obtained',
            decision='PROMISING lead; cannot digitize or claim raw experimental validation from an abstract.',license='Not verified for underlying data'),
        dict(id='P05',title='Laboratory Scale Gear Faults Data',url='https://zenodo.org/records/15265237',language='English',
            evidence='Primary repository description: fault conditions, load conditions and sensor locations',
            measured_TE='not established from metadata',relief_of_same_gear_documented='not established',
            decision='INELIGIBLE at screening stage: fault/vibration data are not a verified relief + TE pair.',license='Not used/downloaded'),
        dict(id='P06',title='High-precision herringbone mesh excitation and tooth-surface modification design data',
            url='https://www.nbsdc.cn/general/dataSetHome?searchKey=%E4%BA%BA%E5%AD%97%E9%BD%BF',language='Mandarin',
            evidence='Indexed Chinese repository description; dynamic detail/download not obtained',
            measured_TE='not verified; description includes LTCA simulations and vibration experiments',
            relief_of_same_gear_documented='not verified from downloaded files',
            decision='UNRESOLVED lead: no raw data obtained; herringbone geometry differs from spur test. Not a validated dataset.',license='Access/use conditions require verification'),
        dict(id='P07',title='Reduction of gear pair TE with tooth profile modification (ISMA 2008)',
            url='https://bura.brunel.ac.uk/handle/2438/3622',language='English',
            evidence='Primary repository abstract: static FE parametric study',measured_TE='not established: described results are FE',
            relief_of_same_gear_documented='model modifications, not certified measurements',
            decision='INELIGIBLE as experimental evidence; potentially useful numerical comparison.',license='Not used/downloaded'),
        dict(id='P08',title='Conceptual modular gear-pair validation rig framework',
            url='https://zenodo.org/records/18921850',language='English',
            evidence='Primary repository expressly states initial conceptual release; datasets are future work',
            measured_TE='no measurement dataset in this release',relief_of_same_gear_documented='no',
            decision='INELIGIBLE: a test-rig design is not measured validation data.',license='Not used/downloaded')]
    sample=[]
    for f in sorted((ROOT/'public_data').glob('*.csv')):
        a=np.genfromtxt(f,delimiter=',',names=True)
        assert a.dtype.names==('theta','q_set','theta_TE')
        assert all(np.all(np.isfinite(a[n])) for n in a.dtype.names)
        sample.append(dict(file=f.name,rows=len(a),columns=list(a.dtype.names),units='radians as repository metadata; no radius conversion',
            theta_range_rad=[float(a['theta'].min()),float(a['theta'].max())],
            TE_range_rad=[float(a['theta_TE'].min()),float(a['theta_TE'].max())],sha256=hashlib.sha256(f.read_bytes()).hexdigest()))
    receipt=dict(screened_sources=sources,downloaded_experimental_samples=sample,
        eligible_public_relief_TE_pairs_found=0,
        conclusion='No eligible public pairing has been obtained in this search. This does not prove no such dataset exists. No relief parameters were fitted to the unrelated robot data.',
        future_eligibility=['same physical pair with profile/relief metrology','sufficient geometry, material and supports','loaded TE waveform and measurement definition','torque, speed and phase indexing','uncertainty/repeats and data-use permission'])
    (ROOT/'public_data_screening.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
    with (ROOT/'public_data_screening.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(sources[0]));w.writeheader();w.writerows(sources)
    print('sources',len(sources),'sample files',len(sample),'eligible',0)


if __name__=='__main__':main()
