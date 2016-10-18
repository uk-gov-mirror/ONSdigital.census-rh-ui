error 404 do
  erb :not_found, locals: { title: I18n.t('404_not_found'),
                            built: @built,
                            commit: @commit,
                            environment: settings.environment }
end

error 500 do
  erb :internal_server_error, locals: { title: I18n.t('500_internal_server_error'),
                                        built: @built,
                                        commit: @commit,
                                        environment: settings.environment }
end
