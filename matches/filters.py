from rest_framework.filters import BaseFilterBackend


class TeamCodesFilterBackend(BaseFilterBackend):
    """
    Filter to find matches between two teams by their country codes.
    """
    def filter_queryset(self, request, queryset, view):
        team1_code = request.query_params.get('team1_code', None)
        team2_code = request.query_params.get('team2_code', None)
        if team1_code is None or team2_code is None:
            return queryset # Needs both teams to filter
        # Filter by country codes
        country_codes = [team1_code, team2_code]
        return queryset.filter(
            team1__country__code_iso3__in=country_codes,
            team2__country__code_iso3__in=country_codes,
        )
