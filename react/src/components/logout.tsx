import React, { useEffect } from "react";
import { Redirect } from "react-router-dom";
import { GET } from "../utils/api_requests";
import { deleteUserID } from "../utils/auth";

export default function Logout() {
  useEffect(() => {
    deleteUserID();
    GET("/logout");
  }, []);

  return <Redirect to="/" />;
}
