"""Run the declared inverse campaign once the complete target is available."""
import time,sys
from inverse_moving_v19 import target,run
while True:
    try:target();break
    except (AssertionError,FileNotFoundError):time.sleep(5)
if '--analytic' in sys.argv:
    from analytic_inverse_v19 import main
    main()
else:
    run(.08,25)
    run(.04,25)
