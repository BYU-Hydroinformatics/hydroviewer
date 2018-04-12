from django.views.decorators.csrf import csrf_exempt
import psycopg2 as pg
import csv


@csrf_exempt
def update_ffgs(request):

    return_obj = {
        'success': "False",
        'message': None,
        'results': {}
    }

    if request.is_ajax() and request.method == 'POST':
        params = request.POST
        file_list = request.FILES.getlist('files')

        conn = pg.connect('host=localhost dbname=hydroviewer_hispaniola user=tethys_default password=pass port=5435')

        cur = conn.cursor()

        cur.execute("""drop table if exists public.ffgs_precip_old;""")

        cur.execute("""create table public.ffgs_precip_old as table public.ffgs_precip;""")

        cur.execute("""truncate table public.ffgs_precip;""")

        cur.copy_from(file_list[0], '"ffgs_precip"', sep=',')

        conn.commit()

        conn.close()

        return_obj['success'] = True

    return JsonResponse(return_obj)