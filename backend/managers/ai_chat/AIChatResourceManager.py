"""AI Chat Resource Manager."""
from datetime import datetime
from abstractions.IResourceManager import IResourceManager
from abstractions.models.ResponseModel import ResponseModel
from abstractions.models.RequestResourceModel import RequestResourceModel
from database.schemas.ai_chat_session import AIChatSessionItem
from database.schemas.ai_chat_message import AIChatMessageItem


class AIChatResourceManager(IResourceManager):
    def get(self, req: RequestResourceModel) -> ResponseModel:
        action = req.data.get("action", "")
        if action == "list_sessions":
            return self._list_sessions(req)
        elif action == "get_session":
            return self._get_session(req)
        elif action == "list_messages":
            return self._list_messages(req)
        elif action == "list_models":
            return self._list_models(req)
        return ResponseModel(success=False, error="Invalid action", status_code=400)

    def post(self, req: RequestResourceModel) -> ResponseModel:
        action = req.data.get("action", "")
        if action == "create_session":
            return self._create_session(req)
        elif action == "send_message":
            return self._send_message(req)
        elif action == "suggest_entry":
            return self._suggest_entry(req)
        elif action == "categorize":
            return self._categorize(req)
        elif action == "update_model_config":
            return self._update_model_config(req)
        return ResponseModel(success=False, error="Invalid action", status_code=400)

    def put(self, req): return ResponseModel(success=False, error="Not implemented", status_code=405)

    def delete(self, req: RequestResourceModel) -> ResponseModel:
        action = req.data.get("action", "")
        if action == "delete_session":
            return self._delete_session(req)
        elif action == "delete_model_config":
            return self._delete_model_config(req)
        return ResponseModel(success=False, error="Invalid action", status_code=400)

    def _get_org_id(self, user_id):
        user = self._db.users.get_by_id(str(user_id))
        return user.get("org_id") if user else None

    def _list_sessions(self, req):
        try:
            user_id = str(req.user_id)
            items = self._db.ai_chat_sessions.list_all(user_id=user_id)
            sessions = [AIChatSessionItem.from_item(i).to_api_dict() for i in items]
            return ResponseModel(success=True, data={"sessions": sessions})
        except Exception as e:
            return ResponseModel(success=False, error=str(e), status_code=500)

    def _create_session(self, req):
        try:
            org_id = self._get_org_id(req.user_id)
            session = AIChatSessionItem(user_id=str(req.user_id), org_id=org_id, title=req.data.get("title", "New Chat"))
            self._db.ai_chat_sessions.create(session.to_item())
            return ResponseModel(success=True, data={"session": session.to_api_dict()}, status_code=201)
        except Exception as e:
            return ResponseModel(success=False, error=str(e), status_code=500)

    def _get_session(self, req):
        try:
            user_id = str(req.user_id)
            session_id = req.data.get("session_id")
            item = self._db.ai_chat_sessions.get_by_key({"user_id": user_id, "id": session_id})
            if not item:
                return ResponseModel(success=False, error="Session not found", status_code=404)
            return ResponseModel(success=True, data={"session": AIChatSessionItem.from_item(item).to_api_dict()})
        except Exception as e:
            return ResponseModel(success=False, error=str(e), status_code=500)

    def _delete_session(self, req):
        try:
            user_id = str(req.user_id)
            session_id = req.data.get("session_id")
            self._db.ai_chat_sessions.delete_by_key({"user_id": user_id, "id": session_id})
            return ResponseModel(success=True, message="Session deleted")
        except Exception as e:
            return ResponseModel(success=False, error=str(e), status_code=500)

    def _list_messages(self, req):
        try:
            session_id = req.data.get("session_id")
            items = self._db.ai_chat_messages.list_all(session_id=session_id)
            messages = [AIChatMessageItem.from_item(i).to_api_dict() for i in items]
            return ResponseModel(success=True, data={"messages": messages})
        except Exception as e:
            return ResponseModel(success=False, error=str(e), status_code=500)

    def _send_message(self, req):
        try:
            session_id = req.data.get("session_id")
            content = req.data.get("content", "")
            model_id = req.data.get("modelId")
            context = req.data.get("context")
            # If context provided, prepend it as system context
            effective_content = content
            if context:
                effective_content = f"[Context: {context}]\n\n{content}"
            user_msg = AIChatMessageItem(session_id=session_id, role="user", content=content)
            self._db.ai_chat_messages.create(user_msg.to_item())
            ai_service = self._service_managers.get("ai")
            if ai_service:
                try:
                    # Build conversation history from previous messages
                    conversation_history = self._build_conversation_history(session_id)
                    ai_response = ai_service.chat(
                        effective_content, session_id, str(req.user_id),
                        conversation_history=conversation_history,
                        model_id=model_id,
                    )
                    ai_msg = AIChatMessageItem(session_id=session_id, role="assistant", content=ai_response.get("content", ""),
                                                chart_config=ai_response.get("chart_config"))
                    self._db.ai_chat_messages.create(ai_msg.to_item())
                    assistant_dict = ai_msg.to_api_dict()
                    assistant_dict["modelId"] = ai_response.get("model_id")
                    return ResponseModel(success=True, data={
                        "userMessage": user_msg.to_api_dict(), "assistantMessage": assistant_dict})
                except Exception as ai_err:
                    print(f"AI chat error: {ai_err}")
                    ai_msg = AIChatMessageItem(session_id=session_id, role="assistant",
                                                content=f"Sorry, I encountered an error: {str(ai_err)}")
                    self._db.ai_chat_messages.create(ai_msg.to_item())
                    return ResponseModel(success=True, data={
                        "userMessage": user_msg.to_api_dict(), "assistantMessage": ai_msg.to_api_dict()})
            return ResponseModel(success=True, data={"userMessage": user_msg.to_api_dict(),
                                                      "assistantMessage": {"content": "AI service unavailable", "role": "assistant"}})
        except Exception as e:
            return ResponseModel(success=False, error=str(e), status_code=500)

    def _build_conversation_history(self, session_id: str) -> list:
        """Fetch recent messages for conversation context."""
        try:
            items = self._db.ai_chat_messages.list_all(session_id=session_id)
            # Return last N messages as {role, content} dicts (exclude the just-saved user message)
            history = []
            for item in items:
                role = item.get("role", "")
                if role in ("user", "assistant"):
                    history.append({"role": role, "content": item.get("content", "")})
            return history
        except Exception:
            return []

    def _suggest_entry(self, req):
        try:
            ai_service = self._service_managers.get("ai")
            if not ai_service:
                return ResponseModel(success=False, error="AI service unavailable", status_code=503)
            suggestion = ai_service.suggest_time_entry(str(req.user_id), req.data)
            return ResponseModel(success=True, data={"suggestion": suggestion})
        except Exception as e:
            return ResponseModel(success=False, error=str(e), status_code=500)

    def _categorize(self, req):
        try:
            ai_service = self._service_managers.get("ai")
            if not ai_service:
                return ResponseModel(success=False, error="AI service unavailable", status_code=503)
            result = ai_service.categorize_entry(req.data.get("description", ""), req.data.get("projects", []))
            return ResponseModel(success=True, data={"categorization": result})
        except Exception as e:
            return ResponseModel(success=False, error=str(e), status_code=500)

    def _list_models(self, req):
        try:
            ai_service = self._service_managers.get("ai")
            if not ai_service:
                return ResponseModel(success=False, error="AI service unavailable", status_code=503)
            models = ai_service.get_active_models()
            return ResponseModel(success=True, data={"models": models})
        except Exception as e:
            return ResponseModel(success=False, error=str(e), status_code=500)

    def _update_model_config(self, req):
        try:
            # Verify super admin
            user_item = self._db.users.get_by_id(str(req.user_id))
            if not user_item or not user_item.get("is_super_admin", False):
                return ResponseModel(success=False, error="Admin access required", status_code=403)

            ai_service = self._service_managers.get("ai")
            if not ai_service:
                return ResponseModel(success=False, error="AI service unavailable", status_code=503)

            model_id = req.data.get("modelId")
            if not model_id:
                return ResponseModel(success=False, error="modelId is required", status_code=400)

            result = ai_service.update_model_config(model_id, req.data)
            return ResponseModel(success=True, data=result, message="Model config updated")
        except Exception as e:
            return ResponseModel(success=False, error=str(e), status_code=500)

    def _delete_model_config(self, req):
        try:
            # Verify super admin
            user_item = self._db.users.get_by_id(str(req.user_id))
            if not user_item or not user_item.get("is_super_admin", False):
                return ResponseModel(success=False, error="Admin access required", status_code=403)

            ai_service = self._service_managers.get("ai")
            if not ai_service:
                return ResponseModel(success=False, error="AI service unavailable", status_code=503)

            model_id = req.data.get("model_id")
            if not model_id:
                return ResponseModel(success=False, error="model_id is required", status_code=400)

            result = ai_service.delete_model_config(model_id)
            return ResponseModel(success=True, data=result, message="Model config reset")
        except Exception as e:
            return ResponseModel(success=False, error=str(e), status_code=500)
