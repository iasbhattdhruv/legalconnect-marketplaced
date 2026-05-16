def language_processor(request):
    language = request.session.get('language', 'en')
    return {
        'current_language': language,
        'available_languages': [
            {'code': 'en', 'label': 'English'},
            {'code': 'hi', 'label': 'Hindi'},
        ]
    }
